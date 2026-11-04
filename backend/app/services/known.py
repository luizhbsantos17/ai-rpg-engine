"""Personagens conhecidos: só o que o PROTAGONISTA sabe sobre os outros (SPEC 6.1).

Informação falsa aparece como "confirmada": o protagonista não sabe que foi enganado.
Status verdadeiros de outros personagens nunca saem daqui.
"""

from __future__ import annotations

from typing import Any

from app.persistence.db import Database
from app.persistence.repositories import CampaignData, CampaignRepository
from app.services.errors import NotFoundError

PLAYER_LEVELS = {"confirmed": "confirmed", "false": "confirmed", "partial": "partial",
                 "estimated": "estimated", "unknown": "unknown"}


class KnownCharactersService:
    def __init__(self, db: Database):
        self.db = db

    def known(self, owner_id: str, campaign_id: str) -> dict[str, Any]:
        with self.db.transaction() as session:
            if CampaignRepository(session, owner_id).get(campaign_id) is None:
                raise NotFoundError("Campanha não encontrada.")
            data = CampaignData(session, campaign_id)
            player = data.entities.player()
            if player is None:
                return {"characters": []}
            by_subject: dict[str, list] = {}
            for record in data.knowledge.known_by(player.id):
                by_subject.setdefault(record.subject, []).append(record)
            characters = []
            for subject, records in by_subject.items():
                entity = data.entities.get(subject)
                if entity is None:  # tema livre ("mapa_perdido"), não um personagem
                    continue
                characters.append({
                    "id": entity.id,
                    "name": entity.name,
                    "kind": entity.kind,
                    "facts": [{"field": r.field, "value": r.known_value, "level": PLAYER_LEVELS.get(r.level, r.level)}
                              for r in records],
                })
            return {"characters": characters}
