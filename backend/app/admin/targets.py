"""Alvos dos comandos: player · npc "Nome" · entity <id> · location "Nome" · "Nome" (qualquer entidade)."""

from __future__ import annotations

from app.persistence.models import Entity
from app.persistence.repositories import CampaignData

KIND_WORDS = {"npc": ("character", "creature"), "location": ("location",)}


class AdminTargetError(ValueError):
    pass


def resolve_target(data: CampaignData, args: list[str], start: int = 0) -> tuple[Entity, int]:
    """Devolve (entidade, quantos argumentos foram usados)."""
    if start >= len(args):
        raise AdminTargetError("Faltou o alvo (ex.: player, npc \"Nome\", entity <id>).")
    word = args[start].lower()
    if word == "player":
        player = data.entities.player()
        if player is None:
            raise AdminTargetError("A campanha ainda não tem protagonista.")
        return player, 1
    if word == "entity":
        entity = data.entities.get(_next(args, start, "o id")) if start + 1 < len(args) else None
        if entity is None:
            raise AdminTargetError("Entidade não encontrada com esse id.")
        return entity, 2
    if word in KIND_WORDS:
        return by_name(data, _next(args, start, "o nome"), KIND_WORDS[word]), 2
    return by_name(data, args[start]), 1


def by_name(data: CampaignData, name: str, kinds: tuple[str, ...] | None = None) -> Entity:
    matches = [e for e in data.entities.list() if e.name.lower() == name.lower() and (kinds is None or e.kind in kinds)]
    if not matches:
        raise AdminTargetError(f"Nada chamado \"{name}\" nesta campanha.")
    if len(matches) > 1:
        options = ", ".join(f"{e.kind} {e.id}" for e in matches)
        raise AdminTargetError(f"Há mais de um \"{name}\": {options}. Use entity <id>.")
    return matches[0]


def _next(args: list[str], start: int, what: str) -> str:
    if start + 1 >= len(args):
        raise AdminTargetError(f"Faltou {what} depois de '{args[start]}'.")
    return args[start + 1]
