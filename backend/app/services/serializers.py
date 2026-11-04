"""Conversão de registros do banco em dicionários para a API.

Só campos que o jogador pode ver: segredos do mestre (gm_secret) nunca saem daqui.
"""

from __future__ import annotations

from typing import Any

from app.persistence.models import Campaign, Message, Turn


def campaign_to_dict(campaign: Campaign) -> dict[str, Any]:
    return {
        "id": campaign.id,
        "title": campaign.title,
        "genre_tags": list(campaign.genre_tags),
        "status": campaign.status,
        "premise": (campaign.intro.player_visible if campaign.intro else {}).get("premise"),
        "created_at": campaign.created_at.isoformat(),
        "updated_at": campaign.updated_at.isoformat(),
    }


def turn_to_dict(turn: Turn) -> dict[str, Any]:
    return {
        "id": turn.id,
        "number": turn.number,
        "status": turn.status,
        "error": turn.error,
        "player_input": turn.player_input,
    }


def message_to_dict(message: Message) -> dict[str, Any]:
    return {
        "id": message.id,
        "seq": message.seq,
        "turn_id": message.turn_id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }
