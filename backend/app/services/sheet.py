"""Ficha do protagonista: o jogador vê o próprio status completo (SPEC 6.1).

Só o protagonista aparece aqui. Status de outros personagens continuam ocultos.
"""

from __future__ import annotations

from typing import Any

from app.engine.time import format_world_time
from app.persistence.db import Database
from app.persistence.repositories import CampaignData, CampaignRepository
from app.services.errors import NotFoundError


class CharacterSheetService:
    def __init__(self, db: Database):
        self.db = db

    def sheet(self, owner_id: str, campaign_id: str) -> dict[str, Any]:
        with self.db.transaction() as session:
            if CampaignRepository(session, owner_id).get(campaign_id) is None:
                raise NotFoundError("Campanha não encontrada.")
            data = CampaignData(session, campaign_id)
            player = data.entities.player()
            if player is None:
                return {"character": None}
            location = data.entities.get(player.location_id) if player.location_id else None
            return {
                "character": {
                    "id": player.id,
                    "name": player.name,
                    "kind": player.kind,
                    "status": player.status,
                    "description": player.data.get("description", ""),
                    "location": location.name if location else None,
                    "attributes": [_attribute(data, a) for a in data.attributes.for_entity(player.id)],
                    "skills": [_skill(data, s) for s in data.skills.for_entity(player.id)],
                    "items": [_item(data, i) for i in data.items.held_by(player.id)],
                    "effects": [_effect(data, e) for e in data.effects.active_for(player.id)],
                },
                "world_time": format_world_time(data.campaign().world_clock),
            }


def _definition_data(data: CampaignData, kind: str, key: str) -> dict[str, Any]:
    definition = data.definitions.current(kind, key)
    return definition.data if definition else {"name": key}


def _attribute(data: CampaignData, attribute) -> dict[str, Any]:
    definition = _definition_data(data, "attribute", attribute.definition_key)
    return {
        "key": attribute.definition_key,
        "name": definition.get("name", attribute.definition_key),
        "description": definition.get("description", ""),
        "value_type": definition.get("value_type", "decimal"),
        "resource": bool(definition.get("resource")),
        "value": attribute.value,
        "max": attribute.max_value,
    }


def _skill(data: CampaignData, skill) -> dict[str, Any]:
    definition = _definition_data(data, "skill", skill.definition_key)
    return {
        "key": skill.definition_key,
        "name": definition.get("name", skill.definition_key),
        "description": definition.get("description", ""),
        "category": definition.get("category"),
        "rarity": definition.get("rarity"),
        "level": skill.level,
        "max_level": definition.get("max_level"),
    }


def _effect(data: CampaignData, effect) -> dict[str, Any]:
    definition = _definition_data(data, "effect", effect.definition_key)
    return {
        "key": effect.definition_key,
        "name": definition.get("name", effect.definition_key),
        "description": definition.get("description", ""),
        "ends": format_world_time(effect.ends_at) if effect.ends_at is not None else None,
    }


def _item(data: CampaignData, item) -> dict[str, Any]:
    definition = _definition_data(data, "item", item.definition_key)
    return {
        "id": item.id,
        "key": item.definition_key,
        "name": definition.get("name", item.definition_key),
        "description": definition.get("description", ""),
        "quantity": item.quantity,
    }
