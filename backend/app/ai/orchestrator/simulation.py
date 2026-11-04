"""Simulação do mundo fora de cena (SPEC 8.1, 8.4, 10.2).

Roda quando um turno faz o tempo avançar pelo menos `AI_SIMULATION_MINUTES` (padrão 6 h):
a IA decide o que os NPCs RELEVANTES (nível de simulação 1) longe do protagonista fizeram
e se houve acontecimentos do mundo. Tudo vira operações validadas pelo motor. NPCs distantes
(nível 2) só avançam por agendamentos; dormentes (3) ficam parados (economia, sem contradição).
O narrador não recebe esses fatos: o protagonista não estava lá.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.ai.prompts.narrator import CampaignBrief
from app.ai.prompts.simulation import build_simulation_messages
from app.ai.structured import request_structured
from app.config import Settings
from app.engine.operations import OperationContext, apply_operations
from app.engine.time import format_duration, format_world_time
from app.engine.witness import NON_WITNESS_KINDS
from app.persistence.db import Database
from app.persistence.models import Entity, Event
from app.persistence.repositories import CampaignData
from app.providers import AIProvider
from app.providers.registry import generation_options

logger = logging.getLogger(__name__)

MAX_SIMULATED_NPCS = 10
SIMULATION_MAX_TOKENS = 600
SIMULATION_ROLE = "simulation"
TIER_RELEVANT = 1


class SimulationOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")
    summary: str = Field(default="", max_length=1000)
    operations: list[dict[str, Any]] = Field(default_factory=list, max_length=30)


class WorldSimulation:
    def __init__(self, db: Database, provider: AIProvider, settings: Settings):
        self.db = db
        self.provider = provider
        self.settings = settings

    def should_run(self, elapsed_minutes: int) -> bool:
        threshold = self.settings.ai_simulation_minutes
        return threshold > 0 and elapsed_minutes >= threshold

    def run(self, campaign_id: str, turn_id: str, model: str, brief: CampaignBrief,
            elapsed_minutes: int, campaign_seed: int) -> dict[str, Any]:
        with self.db.transaction() as session:
            data = CampaignData(session, campaign_id)
            now = data.campaign().world_clock
            npc_lines, aliases = self._relevant_npcs(data)
        messages = build_simulation_messages(brief, format_duration(elapsed_minutes), format_world_time(now), npc_lines)
        options = replace(generation_options(self.settings, model), temperature=0.7,
                          max_output_tokens=SIMULATION_MAX_TOKENS)
        result = request_structured(self.provider, messages, options, SimulationOutput, self.settings.ai_json_attempts)

        with self.db.transaction() as session:
            data = CampaignData(session, campaign_id)
            for attempt in result.attempts:
                data.ai_requests.record(turn_id=turn_id, role=SIMULATION_ROLE, provider=attempt.result.provider,
                                        model=attempt.result.model, tokens_in=attempt.result.tokens_in,
                                        tokens_out=attempt.result.tokens_out, duration_ms=attempt.result.duration_ms,
                                        error=attempt.error, request_messages=[m.to_dict() for m in messages])
            if not result.ok:
                return {"summary": None, "error": result.attempts[-1].error, "outcomes": []}
            ctx = OperationContext(data, source="ai", campaign_seed=campaign_seed, world_time=now, turn_id=turn_id,
                                   refs=dict(aliases), seed_scope="simulacao", inside_schedule=True)
            outcomes = apply_operations(ctx, result.value.operations)
            summary = result.value.summary.strip()
            data.events.record("world.simulated", Event.SOURCE_AI,
                               {"summary": summary, "elapsed_minutes": elapsed_minutes,
                                "applied": sum(o.status == "applied" for o in outcomes),
                                "rejected": sum(o.status == "rejected" for o in outcomes)},
                               turn_id, now)
            if summary:
                turn = data.turns.get(turn_id)
                data.memory_search.index("world", turn_id, turn.number if turn else 0, summary)
            return {"summary": summary, "error": None, "outcomes": [o.to_dict() for o in outcomes]}

    @staticmethod
    def _relevant_npcs(data: CampaignData) -> tuple[list[str], dict[str, str]]:
        player = data.entities.player()
        here = player.location_id if player else None
        npcs = [
            e for e in data.entities.list()
            if not e.is_player and e.status == Entity.STATUS_ACTIVE and e.sim_tier == TIER_RELEVANT
            and e.kind not in NON_WITNESS_KINDS and (here is None or e.location_id != here)
        ][:MAX_SIMULATED_NPCS]
        lines, aliases = [], {}
        for index, npc in enumerate(npcs, start=1):
            alias = f"n{index}"
            aliases[alias] = npc.id
            location = data.entities.get(npc.location_id) if npc.location_id else None
            parts = [f"{alias}: {npc.name} ({npc.kind})", f"local: {location.name if location else 'desconhecido'}"]
            for key, label in (("personality", "personalidade"), ("goal", "objetivo")):
                if npc.data.get(key):
                    parts.append(f"{label}: {str(npc.data[key])[:200]}")
            memories = data.memories.recall(npc.id, 2)
            if memories:
                parts.append("lembra: " + " | ".join(m.content[:150] for m in memories))
            lines.append("- " + "; ".join(parts))
        return lines, aliases
