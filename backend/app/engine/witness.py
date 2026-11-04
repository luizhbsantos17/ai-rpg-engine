"""Memória das testemunhas: quem está na cena lembra do que viu (SPEC 8.2).

Sem chamada extra à IA: depois das mecânicas do turno, cada NPC no mesmo local do
protagonista guarda uma lembrança curta do que presenciou. NPCs em outros lugares não sabem.
"""

from __future__ import annotations

from app.persistence.models import Entity
from app.persistence.repositories import CampaignData

MAX_WITNESSES = 10
MAX_INPUT_CHARS = 240
MAX_FACTS = 3
NON_WITNESS_KINDS = ("location", "region", "building", "container", "vehicle", "faction", "organization")


def scene_npcs(data: CampaignData, player: Entity) -> list[Entity]:
    if not player.location_id:
        return []
    return [
        e for e in data.entities.at_location(player.location_id)
        if not e.is_player and e.status == Entity.STATUS_ACTIVE and e.kind not in NON_WITNESS_KINDS
    ][:MAX_WITNESSES]


def record_witnesses(data: CampaignData, player: Entity, player_input: str, facts: list[str],
                     world_time: int, turn_id: str | None) -> int:
    action = player_input.strip().replace("\n", " ")[:MAX_INPUT_CHARS]
    seen = " ".join(facts[:MAX_FACTS])
    content = f"Viu {player.name} agir: «{action}»." + (f" Resultado: {seen}" if seen else "")
    witnesses = scene_npcs(data, player)
    for npc in witnesses:
        data.memories.remember(npc.id, content, importance=1, world_time=world_time, turn_id=turn_id)
    return len(witnesses)


def scene_knowledge_notes(data: CampaignData, player: Entity, memories_per_npc: int = 3) -> list[str]:
    """Para o narrador: o que cada NPC presente lembra e sabe sobre o protagonista."""
    notes = []
    for npc in scene_npcs(data, player):
        parts = []
        memories = data.memories.recall(npc.id, memories_per_npc)
        if memories:
            parts.append("lembra: " + " | ".join(m.content for m in memories))
        known = data.knowledge.known_by(npc.id, player.id)
        if known:
            parts.append(f"sabe sobre {player.name}: " + ", ".join(
                f"{k.field}={k.known_value or '?'} ({k.level})" for k in known
            ))
        notes.append(f"{npc.name}: " + ("; ".join(parts) if parts else "não sabe nada especial sobre o protagonista"))
    return notes
