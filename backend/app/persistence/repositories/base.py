"""Base dos repositórios de dados de jogo (sempre presos a uma campanha)."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.persistence.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class CampaignMismatchError(Exception):
    """Tentativa de gravar um dado de uma campanha usando o repositório de outra."""


class CampaignScopedRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: Session, campaign_id: str):
        if not campaign_id:
            raise ValueError("campaign_id é obrigatório para acessar dados de jogo.")
        self.session = session
        self.campaign_id = campaign_id

    def _select(self) -> Select[tuple[ModelT]]:
        """Toda consulta começa aqui, já filtrada pela campanha."""
        return select(self.model).where(self.model.campaign_id == self.campaign_id)

    def get(self, record_id: str) -> ModelT | None:
        return self.session.scalars(self._select().where(self.model.id == record_id)).first()

    def count(self) -> int:
        query = select(func.count()).select_from(self.model).where(
            self.model.campaign_id == self.campaign_id
        )
        return self.session.scalar(query) or 0

    def add(self, record: ModelT) -> ModelT:
        if record.campaign_id is None:
            record.campaign_id = self.campaign_id
        elif record.campaign_id != self.campaign_id:
            raise CampaignMismatchError(
                f"{self.model.__name__} pertence a outra campanha; gravação recusada."
            )
        self.session.add(record)
        # Grava já (dentro da transação) para manter a ordem e detectar erros cedo.
        self.session.flush()
        return record

    def _next_value(self, column) -> int:
        """Próximo número sequencial desta campanha para a coluna (ex.: turns.number)."""
        query = select(func.max(column)).where(self.model.campaign_id == self.campaign_id)
        return (self.session.scalar(query) or 0) + 1
