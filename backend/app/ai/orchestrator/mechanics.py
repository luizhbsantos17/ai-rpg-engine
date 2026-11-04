"""Fase de mecânicas do turno (D-013): IA intérprete → motor valida, rola e aplica.

1. Se a campanha ainda não tem protagonista: preparação (regras básicas, protagonista, local).
2. Intérprete: a ação do jogador vira operações (JSON validado, com reenvio do erro — D-008).
3. Motor: `apply_operations` numa transação (cada operação no seu savepoint).
4. Resultado guardado no turno (`turns.mechanics`): repetir o turno não aplica de novo.

Nenhuma chamada à IA acontece com transação aberta (D-012).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from typing import Any

from app.ai.context.game_state import build_game_state
from app.ai.context.narration import HistoryItem
from app.ai.prompts.interpreter import build_interpreter_messages
from app.ai.prompts.narrator import CampaignBrief
from app.ai.prompts.setup import build_setup_messages
from app.ai.schemas.interpreter import InterpreterOutput
from app.ai.schemas.setup import CampaignSetup
from app.ai.structured import StructuredResult, request_structured
from app.config import Settings
from app.engine.notifications import describe_for_narrator, player_notices
from app.engine.witness import record_witnesses, scene_knowledge_notes
from app.engine.operations import OperationContext, OperationOutcome, apply_operations
from app.persistence.db import Database
from app.persistence.models import Message
from app.persistence.repositories import CampaignData
from app.providers import AIProvider, ChatMessage
from app.providers.registry import generation_options
from app.services.serializers import message_to_dict

logger = logging.getLogger(__name__)

RECENT_HISTORY_FOR_INTERPRETER = 4
INTERPRETER_TEMPERATURE = 0.3  # regras pedem consistência, não criatividade
# Limites próprios de tamanho: JSON de operações é curto. Sem isso, modelos pequenos às vezes
# "disparam" até o limite da narração e o JSON sai cortado (medido com qwen2.5:1.5b em 2026-11-04).
INTERPRETER_MAX_TOKENS = 512
SETUP_MAX_TOKENS = 800


@dataclass
class MechanicsInput:
    """Montado na preparação do turno (dentro da transação curta)."""

    brief: CampaignBrief
    recent_history: list[HistoryItem]
    player_input: str
    campaign_seed: int
    world_time: int
    stored: dict[str, Any] | None = None  # turno repetido: mecânicas já aplicadas antes


@dataclass
class MechanicsResult:
    narrator_facts: list[str] = field(default_factory=list)
    system_messages: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    scene_notes: list[str] = field(default_factory=list)  # o que cada NPC presente sabe e lembra


class MechanicsPhase:
    def __init__(self, db: Database, provider: AIProvider, settings: Settings):
        self.db = db
        self.provider = provider
        self.settings = settings

    def run(self, campaign_id: str, turn_id: str, model: str, mechanics: MechanicsInput) -> MechanicsResult:
        """Erros do provedor (conexão, tempo esgotado) sobem; JSON inválido não interrompe o turno."""
        if mechanics.stored is not None:
            return MechanicsResult(mechanics.stored.get("narrator_facts", []), [], mechanics.stored,
                                   mechanics.stored.get("scene_notes", []))

        base = replace(generation_options(self.settings, model), temperature=INTERPRETER_TEMPERATURE)
        setup_options = replace(base, max_output_tokens=min(base.max_output_tokens or SETUP_MAX_TOKENS, SETUP_MAX_TOKENS))
        options = replace(base, max_output_tokens=min(base.max_output_tokens or INTERPRETER_MAX_TOKENS,
                                                      INTERPRETER_MAX_TOKENS))
        summary: dict[str, Any] = {"setup": None, "intent": None, "interpreter_error": None, "outcomes": []}
        outcomes: list[OperationOutcome] = []

        if self._needs_setup(campaign_id):
            setup = request_structured(self.provider, build_setup_messages(mechanics.brief), setup_options,
                                       CampaignSetup, self.settings.ai_json_attempts)
            self._record_attempts(campaign_id, turn_id, "setup", setup, build_setup_messages(mechanics.brief))
            if setup.ok:
                outcomes += self._apply(campaign_id, turn_id, mechanics, setup.value.to_operations(), {})
                summary["setup"] = "applied"
            else:
                summary["setup"] = "failed: " + (setup.attempts[-1].error or "")

        state_text, aliases = self._game_state(campaign_id)
        messages = build_interpreter_messages(mechanics.brief, state_text, mechanics.recent_history, mechanics.player_input)
        interpretation = request_structured(self.provider, messages, options, InterpreterOutput,
                                            self.settings.ai_json_attempts)
        self._record_attempts(campaign_id, turn_id, "interpreter", interpretation, messages)
        operations: list = []
        if interpretation.ok:
            summary["intent"] = interpretation.value.intent
            operations = interpretation.value.operations
        else:
            summary["interpreter_error"] = interpretation.attempts[-1].error
        return self._apply_and_save(campaign_id, turn_id, mechanics, operations, aliases, outcomes, summary)

    # ---------- partes com banco (transações curtas) ----------

    def _needs_setup(self, campaign_id: str) -> bool:
        with self.db.transaction() as session:
            return CampaignData(session, campaign_id).entities.player() is None

    def _game_state(self, campaign_id: str):
        with self.db.transaction() as session:
            snapshot = build_game_state(CampaignData(session, campaign_id))
            return snapshot.text, snapshot.aliases

    def _apply(self, campaign_id, turn_id, mechanics: MechanicsInput, operations, aliases) -> list[OperationOutcome]:
        with self.db.transaction() as session:
            ctx = OperationContext(
                CampaignData(session, campaign_id), source="ai", campaign_seed=mechanics.campaign_seed,
                world_time=mechanics.world_time, turn_id=turn_id, refs=dict(aliases),
            )
            return apply_operations(ctx, operations)

    def _apply_and_save(self, campaign_id, turn_id, mechanics: MechanicsInput, operations, aliases,
                        prior: list[OperationOutcome], summary: dict[str, Any]) -> MechanicsResult:
        """Aplica as operações do intérprete e guarda o resumo no turno NA MESMA transação.

        Assim, se o programa cair no meio, ou tudo ficou gravado (e repetir o turno não aplica
        de novo) ou nada ficou (e repetir aplica uma vez só).
        """
        with self.db.transaction() as session:
            data = CampaignData(session, campaign_id)
            ctx = OperationContext(
                data, source="ai", campaign_seed=mechanics.campaign_seed,
                world_time=mechanics.world_time, turn_id=turn_id, refs=dict(aliases),
            )
            outcomes = prior + apply_operations(ctx, operations)
            facts = describe_for_narrator(outcomes)
            summary["outcomes"] = [o.to_dict() for o in outcomes]
            summary["narrator_facts"] = facts
            player = data.entities.player()
            messages = [
                data.messages.append(Message.ROLE_SYSTEM, notice.as_message(), turn_id)
                for notice in player_notices(outcomes, player.id if player else None)
            ]
            if player is not None:
                record_witnesses(data, player, mechanics.player_input, facts, data.campaign().world_clock, turn_id)
                summary["scene_notes"] = scene_knowledge_notes(data, player)
            turn = data.turns.get(turn_id)
            if turn is not None:
                turn.mechanics = summary
                session.flush()
            return MechanicsResult(facts, [message_to_dict(m) for m in messages], summary,
                                   summary.get("scene_notes", []))

    def _record_attempts(self, campaign_id, turn_id, role: str, result: StructuredResult, messages: list[ChatMessage]):
        with self.db.transaction() as session:
            data = CampaignData(session, campaign_id)
            for attempt in result.attempts:
                data.ai_requests.record(
                    turn_id=turn_id, role=role, provider=attempt.result.provider, model=attempt.result.model,
                    tokens_in=attempt.result.tokens_in, tokens_out=attempt.result.tokens_out,
                    duration_ms=attempt.result.duration_ms, error=attempt.error,
                    request_messages=[m.to_dict() for m in messages],
                )
