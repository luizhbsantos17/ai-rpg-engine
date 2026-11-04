"""Contexto de aplicação de uma lista de operações (um turno, um comando admin...)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from app.engine.dice import derive_seed
from app.engine.errors import OperationRejected
from app.persistence.models import Entity, ItemInstance
from app.persistence.repositories import CampaignData

PLAYER_REF = "player"


@dataclass
class OperationContext:
    data: CampaignData
    source: str  # "ai" | "admin" | "system"
    campaign_seed: int
    world_time: int = 0
    turn_id: str | None = None
    # apelidos criados nesta lista ("goblin_1" -> id real) e resultados de testes por apelido
    refs: dict[str, str] = field(default_factory=dict)
    check_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    # Escopo da semente: rolagens de um acontecimento agendado não repetem as do turno.
    seed_scope: str = "turno"
    inside_schedule: bool = False  # operações disparadas por um agendamento (não podem avançar o tempo)
    _roll_counter: int = 0

    def next_seed(self) -> int:
        """Semente determinística por rolagem: (semente da campanha, turno, escopo, nº da rolagem)."""
        self._roll_counter += 1
        return derive_seed(self.campaign_seed, self.turn_id or "sem-turno", self.seed_scope, self._roll_counter)

    def child(self, source: str, world_time: int, seed_scope: str) -> OperationContext:
        """Contexto para operações disparadas por um acontecimento agendado."""
        return OperationContext(self.data, source=source, campaign_seed=self.campaign_seed, world_time=world_time,
                                turn_id=self.turn_id, seed_scope=seed_scope, inside_schedule=True)

    def register_ref(self, ref: str | None, record_id: str) -> None:
        if not ref:
            return
        if ref in self.refs or ref == PLAYER_REF or _looks_like_id(ref):
            raise OperationRejected(f"O apelido '{ref}' já está em uso ou é reservado.")
        self.refs[ref] = record_id

    def entity(self, ref: str, allow_dead: bool = True) -> Entity:
        if ref == PLAYER_REF:
            entity = self.data.entities.player()
            if entity is None:
                raise OperationRejected("A campanha ainda não tem protagonista.")
        else:
            entity = self.data.entities.get(self.refs.get(ref, ref))
        if entity is None or entity.status == Entity.STATUS_REMOVED:
            raise OperationRejected(f"Entidade '{ref}' não existe nesta campanha.")
        if not allow_dead and entity.status == Entity.STATUS_DEAD:
            raise OperationRejected(f"'{entity.name}' está morto(a).")
        return entity

    def item(self, ref: str) -> ItemInstance:
        item = self.data.items.get(self.refs.get(ref, ref))
        if item is None or item.status != ItemInstance.STATUS_ACTIVE:
            raise OperationRejected(f"Item '{ref}' não existe (ou já foi destruído) nesta campanha.")
        return item


def _looks_like_id(text: str) -> bool:
    try:
        uuid.UUID(text)
        return True
    except ValueError:
        return False
