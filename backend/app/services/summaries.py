"""Memória narrativa: a cada N turnos concluídos, a IA resume o trecho (SPEC 15.1).

Roda depois do turno, em segundo plano (não atrasa o jogador). Nos testes roda na hora.
Se falhar (IA indisponível), tenta de novo depois do próximo turno: nada se perde,
porque o histórico completo continua no banco.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import replace

from app.ai.prompts.summarizer import build_summarizer_messages
from app.config import Settings
from app.persistence.db import Database
from app.persistence.models import Message, Summary, Turn
from app.persistence.repositories import CampaignData
from app.providers import AIProvider, ProviderError
from app.providers.registry import generation_options, resolve_model

logger = logging.getLogger(__name__)

SUMMARY_MAX_TOKENS = 400
SUMMARIZER_ROLE = "summarizer"


class SummaryService:
    def __init__(self, db: Database, provider: AIProvider, settings: Settings):
        self.db = db
        self.provider = provider
        self.settings = settings
        self._lock = threading.Lock()  # um resumo por vez (evita resumir o mesmo trecho duas vezes)

    def schedule(self, campaign_id: str) -> None:
        """Chamado ao fim de cada turno concluído."""
        if self.settings.ai_summary_every <= 0:
            return
        self._in_background(lambda: self.maybe_summarize(campaign_id))

    def _in_background(self, task: Callable[[], object]) -> None:
        if self.settings.app_env == "test":
            task()
            return
        threading.Thread(target=self._safe, args=(task,), daemon=True, name="resumo-campanha").start()

    @staticmethod
    def _safe(task: Callable[[], object]) -> None:
        try:
            task()
        except Exception:
            logger.exception("Falha ao gerar resumo da campanha (será tentado de novo depois).")

    def maybe_summarize(self, campaign_id: str) -> Summary | None:
        if not self._lock.acquire(blocking=False):
            return None
        try:
            return self._summarize_next_chunk(campaign_id)
        finally:
            self._lock.release()

    def _summarize_next_chunk(self, campaign_id: str) -> Summary | None:
        every = self.settings.ai_summary_every
        with self.db.transaction() as session:
            data = CampaignData(session, campaign_id)
            title = data.campaign().title
            last = data.summaries.last_covered_turn()
            pending = [t for t in data.turns.list_ordered() if t.number > last and t.status == Turn.STATUS_COMPLETED]
            if len(pending) < every:
                return None
            chunk = pending[:every]
            turns = []
            for turn in chunk:
                narration = next((m.content for m in data.messages.for_turn(turn.id)
                                  if m.role == Message.ROLE_NARRATION), "")
                turns.append((turn.number, turn.player_input, narration))

        messages = build_summarizer_messages(title, turns)
        model = resolve_model(self.provider, self.settings.ai_model)
        options = replace(generation_options(self.settings, model), max_output_tokens=SUMMARY_MAX_TOKENS,
                          temperature=0.3)
        try:
            result = self.provider.complete(messages, options)
        except ProviderError as exc:
            logger.warning("Resumo adiado: %s", exc.message)
            return None
        text = result.text.strip()
        if not text:
            return None

        with self.db.transaction() as session:
            data = CampaignData(session, campaign_id)
            if data.summaries.last_covered_turn() >= chunk[-1].number:
                return None  # outro processo já resumiu
            summary = data.summaries.add(Summary(scope="scene", from_turn=chunk[0].number,
                                                 to_turn=chunk[-1].number, content=text))
            data.memory_search.index("summary", summary.id, summary.to_turn, text)
            data.ai_requests.record(role=SUMMARIZER_ROLE, provider=result.provider, model=result.model,
                                    tokens_in=result.tokens_in, tokens_out=result.tokens_out,
                                    duration_ms=result.duration_ms,
                                    request_messages=[m.to_dict() for m in messages])
            return summary
