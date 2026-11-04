"""Mapa, diário e laços do ponto de vista do PROTAGONISTA (SPEC 12.1).

- Mapa: lugares visitados; no local atual, quem e o que está à vista (nomes, nunca status).
- Diário: resumos da história + avisos importantes (missões e alertas), em ordem.
- Laços: as relações do próprio protagonista (o que os outros sentem por ele continua oculto).
"""

from __future__ import annotations

from typing import Any

from app.persistence.db import Database
from app.persistence.models import Entity, Message
from app.persistence.repositories import CampaignData, CampaignRepository
from app.services.errors import NotFoundError

DIARY_TAGS = ("[MISSÃO]", "[ALERTA]")
MAX_DIARY_NOTICES = 60


class JournalService:
    def __init__(self, db: Database):
        self.db = db

    def journal(self, owner_id: str, campaign_id: str) -> dict[str, Any]:
        with self.db.transaction() as session:
            if CampaignRepository(session, owner_id).get(campaign_id) is None:
                raise NotFoundError("Campanha não encontrada.")
            data = CampaignData(session, campaign_id)
            player = data.entities.player()
            if player is None:
                return {"map": {"current": None, "places": []}, "diary": [], "bonds": []}
            return {"map": self._map(data, player), "diary": self._diary(data), "bonds": self._bonds(data, player)}

    @staticmethod
    def _map(data: CampaignData, player: Entity) -> dict[str, Any]:
        current = data.entities.get(player.location_id) if player.location_id else None
        places = [
            {"id": e.id, "name": e.name, "kind": e.kind, "description": str(e.data.get("description", ""))[:300],
             "current": current is not None and e.id == current.id}
            for e in data.entities.list() if e.data.get("visited_by_player")
        ]
        here = None
        if current is not None:
            present = [e for e in data.entities.at_location(current.id) if not e.is_player]
            here = {
                "id": current.id, "name": current.name,
                "present": [{"name": e.name, "kind": e.kind, "status": "caído" if e.status == "dead" else ""}
                            for e in present],
                "items": [{"key": i.definition_key, "name": _item_name(data, i.definition_key), "quantity": i.quantity}
                          for i in data.items.at_location(current.id)],
            }
        return {"current": here, "places": places}

    @staticmethod
    def _diary(data: CampaignData) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for summary in data.summaries.latest(50):
            entries.append({"kind": "summary", "turn": summary.to_turn, "text": summary.content,
                            "from_turn": summary.from_turn})
        notices = [m for m in data.messages.with_role(Message.ROLE_SYSTEM)
                   if m.content.startswith(DIARY_TAGS)][-MAX_DIARY_NOTICES:]
        turn_numbers = {}
        for message in notices:
            if message.turn_id and message.turn_id not in turn_numbers:
                turn = data.turns.get(message.turn_id)
                turn_numbers[message.turn_id] = turn.number if turn else 0
            entries.append({"kind": "notice", "turn": turn_numbers.get(message.turn_id, 0), "text": message.content})
        return sorted(entries, key=lambda e: (e["turn"], e["kind"] != "summary"))

    @staticmethod
    def _bonds(data: CampaignData, player: Entity) -> list[dict[str, Any]]:
        bonds = []
        for relationship in data.relationships.involving(player.id):
            if relationship.source_id != player.id:
                continue  # sentimentos dos outros pelo protagonista são ocultos
            other = data.entities.get(relationship.target_id)
            if other is None:
                continue
            bonds.append({"name": other.name, "labels": list(relationship.labels),
                          "dimensions": dict(relationship.dimensions)})
        return bonds


def _item_name(data: CampaignData, key: str) -> str:
    definition = data.definitions.current("item", key)
    return definition.data.get("name", key) if definition else key
