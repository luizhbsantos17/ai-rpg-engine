"""Orquestrador do turno (Etapa 1): entrada → contexto → IA → narração salva.

Fases (D-012: a IA nunca é chamada com transação aberta):
1. `prepare`: em uma transação curta, registra o turno como `processing` e monta o contexto.
   Erros de pedido (campanha inexistente, turno em andamento...) aparecem aqui, antes do stream.
2. `run`: chama a IA fora de transação e repassa o texto aos poucos.
3. No fim, em UMA transação: narração + registro da chamada à IA + evento + turno `completed`.
   Se algo falhar (ou a conexão cair), o turno vira `failed` e pode ser repetido com o mesmo id.

Idempotência: o `turn_id` vem do frontend. Repetir um turno concluído devolve a narração
já gravada, sem chamar a IA de novo; repetir um turno que falhou tenta de novo.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.ai.context.narration import HistoryItem, build_narration_context
from app.ai.orchestrator.events import (
    MechanicsApplied,
    NarrationDelta,
    TurnCompleted,
    TurnEvent,
    TurnFailed,
    TurnStarted,
)
from app.ai.orchestrator.mechanics import MechanicsInput, MechanicsPhase
from app.ai.prompts.narrator import CampaignBrief
from app.config import Settings
from app.persistence.db import Database
from app.persistence.models import Event, Message, Turn
from app.persistence.repositories import CampaignData, CampaignRepository
from app.providers import (
    AIProvider,
    ChatMessage,
    CompletionResult,
    ProviderError,
    ProviderResponseError,
    StreamCompleted,
    TextDelta,
)
from app.providers.registry import generation_options, resolve_model
from app.services.errors import ConflictError, InvalidInputError, NotFoundError
from app.services.serializers import message_to_dict, turn_to_dict

logger = logging.getLogger(__name__)

MAX_INPUT_CHARS = 4000
HISTORY_FETCH_LIMIT = 60
RECENT_FOR_INTERPRETER = 4
CANON_IN_CONTEXT = 40
NARRATOR_ROLE = "narrator"
INTERRUPTED_MESSAGE = "Jogada interrompida antes do fim (conexão encerrada). Tente de novo."
INTERNAL_ERROR_MESSAGE = "Erro interno ao processar a jogada. Tente de novo; se persistir, veja o log do servidor."


@dataclass
class PreparedTurn:
    owner_id: str
    campaign_id: str
    turn: dict[str, Any]
    player_message: dict[str, Any]
    world_time: int
    player_input: str = ""
    brief: CampaignBrief | None = None
    history: list[HistoryItem] = field(default_factory=list)
    mechanics: MechanicsInput | None = None  # None = motor desligado (AI_MECHANICS=false)
    context: list[ChatMessage] = field(default_factory=list)  # montado depois das mecânicas
    replay_narration: dict[str, Any] | None = None
    replay_system_messages: list[dict[str, Any]] = field(default_factory=list)


class TurnOrchestrator:
    def __init__(self, db: Database, provider: AIProvider, settings: Settings):
        self.db = db
        self.provider = provider
        self.settings = settings
        self.mechanics = MechanicsPhase(db, provider, settings)

    # ---------- fase 1 ----------

    def prepare(self, owner_id: str, campaign_id: str, turn_id: str, player_input: str) -> PreparedTurn:
        player_input = (player_input or "").strip()
        self._validate(turn_id, player_input)
        if self.provider.is_paid and self.settings.ai_spend_limit_per_session <= 0:
            raise ConflictError(
                "O provedor de IA configurado é pago e o limite de gasto (AI_SPEND_LIMIT_PER_SESSION) é 0."
            )
        try:
            with self.db.transaction() as session:
                campaign = CampaignRepository(session, owner_id).get(campaign_id)
                if campaign is None:
                    raise NotFoundError("Campanha não encontrada.")
                data = CampaignData(session, campaign_id)
                turn = data.turns.get(turn_id)
                if turn is None:
                    turn, player_message = self._start_new_turn(data, turn_id, player_input, campaign.world_clock)
                else:
                    player_message, narration = self._existing_turn_messages(data, turn, player_input)
                    if turn.status == Turn.STATUS_COMPLETED:
                        notices = [m for m in data.messages.for_turn(turn.id) if m.role == Message.ROLE_SYSTEM]
                        return PreparedTurn(
                            owner_id, campaign_id, turn_to_dict(turn), message_to_dict(player_message),
                            campaign.world_clock, replay_narration=message_to_dict(narration),
                            replay_system_messages=[message_to_dict(m) for m in notices],
                        )
                    self._retry_failed_turn(data, turn, campaign.world_clock)

                history = [
                    HistoryItem(m.role, m.content)
                    for m in data.messages.recent_from_completed_turns(HISTORY_FETCH_LIMIT)
                ]
                brief = CampaignBrief(
                    title=campaign.title,
                    genre_tags=list(campaign.genre_tags),
                    player_visible=dict(campaign.intro.player_visible) if campaign.intro else {},
                    gm_secret=dict(campaign.intro.gm_secret) if campaign.intro else {},
                    canon=[(f.status, f.statement) for f in data.canon.list_current(CANON_IN_CONTEXT)],
                )
                mechanics = None
                if self.settings.ai_mechanics:
                    recent = [h for h in history if h.role in (Message.ROLE_PLAYER, Message.ROLE_NARRATION)]
                    mechanics = MechanicsInput(
                        brief, recent[-RECENT_FOR_INTERPRETER:], player_input, campaign.rng_seed,
                        campaign.world_clock, stored=turn.mechanics,
                    )
                return PreparedTurn(
                    owner_id, campaign_id, turn_to_dict(turn), message_to_dict(player_message),
                    campaign.world_clock, player_input=player_input, brief=brief, history=history,
                    mechanics=mechanics,
                )
        except IntegrityError:
            # Mesmo id de turno usado em outra campanha, ou duas jogadas simultâneas.
            raise ConflictError("Não foi possível registrar a jogada: identificador já usado ou jogada simultânea.") from None

    @staticmethod
    def _validate(turn_id: str, player_input: str) -> None:
        try:
            uuid.UUID(str(turn_id))
        except ValueError:
            raise InvalidInputError("turn_id precisa ser um UUID.") from None
        if not player_input:
            raise InvalidInputError("Escreva o que seu personagem faz ou diz.")
        if len(player_input) > MAX_INPUT_CHARS:
            raise InvalidInputError(f"Texto longo demais (máximo {MAX_INPUT_CHARS} caracteres).")

    @staticmethod
    def _start_new_turn(data: CampaignData, turn_id: str, player_input: str, world_time: int):
        if data.turns.find_processing() is not None:
            raise ConflictError("Já existe uma jogada em andamento nesta campanha. Aguarde terminar.")
        turn = data.turns.create(turn_id, player_input)
        player_message = data.messages.append(Message.ROLE_PLAYER, player_input, turn.id)
        data.events.record("turn.started", Event.SOURCE_SYSTEM, {"number": turn.number}, turn.id, world_time)
        return turn, player_message

    @staticmethod
    def _existing_turn_messages(data: CampaignData, turn: Turn, player_input: str):
        if turn.player_input != player_input:
            raise ConflictError("Este identificador de jogada já foi usado com outro texto.")
        if turn.status == Turn.STATUS_PROCESSING:
            raise ConflictError("Esta jogada ainda está em andamento.")
        messages = data.messages.for_turn(turn.id)
        player_message = next(m for m in messages if m.role == Message.ROLE_PLAYER)
        narration = next((m for m in reversed(messages) if m.role == Message.ROLE_NARRATION), None)
        return player_message, narration

    @staticmethod
    def _retry_failed_turn(data: CampaignData, turn: Turn, world_time: int) -> None:
        latest = data.turns.latest()
        if latest is not None and latest.number != turn.number:
            raise ConflictError("Só é possível repetir a jogada mais recente; esta já foi seguida por outras.")
        if data.turns.find_processing() is not None:
            raise ConflictError("Já existe uma jogada em andamento nesta campanha. Aguarde terminar.")
        data.turns.mark_processing(turn)
        data.events.record("turn.retried", Event.SOURCE_SYSTEM, {"number": turn.number}, turn.id, world_time)

    # ---------- fases 2 e 3 ----------

    def run(self, prepared: PreparedTurn) -> Iterator[TurnEvent]:
        replay = prepared.replay_narration is not None
        yield TurnStarted(prepared.turn, prepared.player_message, replay=replay)
        if replay:
            if prepared.replay_system_messages:
                yield MechanicsApplied(prepared.replay_system_messages)
            yield NarrationDelta(prepared.replay_narration["content"])
            yield TurnCompleted(prepared.turn, prepared.replay_narration)
            return

        finished = False
        model: str | None = None
        started = time.monotonic()
        try:
            model = resolve_model(self.provider, self.settings.ai_model)
            facts: list[str] = []
            if prepared.mechanics is not None:
                outcome = self.mechanics.run(prepared.campaign_id, prepared.turn["id"], model, prepared.mechanics)
                facts = outcome.narrator_facts
                if outcome.system_messages or outcome.summary.get("intent"):
                    yield MechanicsApplied(outcome.system_messages, outcome.summary.get("intent"))
            prepared.context = build_narration_context(
                prepared.brief, prepared.history, prepared.player_input,
                self.settings.ai_context_window, self.settings.ai_max_output_tokens,
                mechanics=prepared.mechanics is not None, facts=facts,
            )
            result: CompletionResult | None = None
            for event in self.provider.stream(prepared.context, generation_options(self.settings, model)):
                if isinstance(event, TextDelta):
                    yield NarrationDelta(event.text)
                elif isinstance(event, StreamCompleted):
                    result = event.result
            if result is None:
                raise ProviderResponseError("A resposta da IA terminou sem ser concluída.")
            if not result.text.strip():
                raise ProviderResponseError("A IA devolveu uma narração vazia.")
            turn, narration = self._save_success(prepared, result)
            finished = True
            yield TurnCompleted(turn, narration)
        except ProviderError as exc:
            turn = self._save_failure(prepared, exc.message, model, started)
            finished = True
            yield TurnFailed(turn, exc.message, exc.retryable)
        except Exception:
            logger.exception("Erro inesperado no turno %s", prepared.turn["id"])
            turn = self._save_failure(prepared, INTERNAL_ERROR_MESSAGE, model, started)
            finished = True
            yield TurnFailed(turn, INTERNAL_ERROR_MESSAGE, True)
        finally:
            if not finished:
                # O consumidor parou de ler (ex.: o navegador fechou a conexão).
                self._save_failure(prepared, INTERRUPTED_MESSAGE, model, started)

    def _save_success(self, prepared: PreparedTurn, result: CompletionResult):
        with self.db.transaction() as session:
            data = CampaignData(session, prepared.campaign_id)
            turn = data.turns.get(prepared.turn["id"])
            if turn is None:
                raise NotFoundError("A campanha foi apagada durante a jogada.")
            narration = data.messages.append(Message.ROLE_NARRATION, result.text, turn.id)
            ai_request = data.ai_requests.record(
                turn_id=turn.id,
                role=NARRATOR_ROLE,
                provider=result.provider,
                model=result.model,
                tokens_in=result.tokens_in,
                tokens_out=result.tokens_out,
                duration_ms=result.duration_ms,
                request_messages=[m.to_dict() for m in prepared.context],
            )
            data.events.record(
                "turn.completed",
                Event.SOURCE_SYSTEM,
                {"number": turn.number, "narration_message_id": narration.id, "ai_request_id": ai_request.id},
                turn.id,
                prepared.world_time,
            )
            data.turns.mark_completed(turn)
            campaigns = CampaignRepository(session, prepared.owner_id)
            campaign = campaigns.get(prepared.campaign_id)
            if campaign is not None:
                campaigns.touch(campaign)
            return turn_to_dict(turn), message_to_dict(narration)

    def _save_failure(self, prepared: PreparedTurn, error: str, model: str | None, started: float) -> dict[str, Any]:
        try:
            with self.db.transaction() as session:
                data = CampaignData(session, prepared.campaign_id)
                turn = data.turns.get(prepared.turn["id"])
                if turn is None:
                    return {**prepared.turn, "status": Turn.STATUS_FAILED, "error": error}
                data.turns.mark_failed(turn, error)
                data.ai_requests.record(
                    turn_id=turn.id,
                    role=NARRATOR_ROLE,
                    provider=self.provider.name,
                    model=model or "(não definido)",
                    duration_ms=int((time.monotonic() - started) * 1000),
                    error=error,
                    request_messages=[m.to_dict() for m in prepared.context],
                )
                data.events.record(
                    "turn.failed", Event.SOURCE_SYSTEM, {"number": turn.number, "error": error},
                    turn.id, prepared.world_time,
                )
                return turn_to_dict(turn)
        except Exception:
            # Nunca deixar a falha ao registrar uma falha derrubar o servidor.
            # Se o programa reiniciar, o turno `processing` vira `failed` (D-012).
            logger.exception("Não foi possível registrar a falha do turno %s", prepared.turn["id"])
            return {**prepared.turn, "status": Turn.STATUS_FAILED, "error": error}
