"""Entidades do mundo e o estado delas: atributos, habilidades, itens e efeitos."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base, CampaignScopedMixin, CreatedAtMixin, IdMixin
from app.persistence.types import UTCDateTime, utc_now


class Entity(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    """Personagem, criatura, local, facção, organização, divindade... (o tipo é livre)."""

    __tablename__ = "entities"

    STATUS_ACTIVE = "active"
    STATUS_DEAD = "dead"
    STATUS_REMOVED = "removed"

    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Nada é apagado de verdade: mortos e removidos mudam de status (DATABASE.md).
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=STATUS_ACTIVE)
    location_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="SET NULL"), index=True
    )
    is_player: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    player_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    sim_tier: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utc_now, onupdate=utc_now)


class EntityAttribute(IdMixin, CampaignScopedMixin, Base):
    """Valor de um atributo de uma entidade. Valores em texto (Decimal ou nominal, sem teto)."""

    __tablename__ = "entity_attributes"
    __table_args__ = (UniqueConstraint("entity_id", "definition_key"),)

    entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    definition_key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    # Só para recursos (vida, mana...): valor máximo atual.
    max_value: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utc_now, onupdate=utc_now)


class EntitySkill(IdMixin, CampaignScopedMixin, Base):
    __tablename__ = "entity_skills"
    __table_args__ = (UniqueConstraint("entity_id", "definition_key"),)

    entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    definition_key: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    acquired_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utc_now)


class ItemInstance(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    """Um item concreto. Fica com UM dono (entidade) OU em UM local — nunca duplicado."""

    __tablename__ = "item_instances"

    STATUS_ACTIVE = "active"
    STATUS_DESTROYED = "destroyed"

    definition_key: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("entities.id", ondelete="SET NULL"), index=True)
    location_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("entities.id", ondelete="SET NULL"), index=True)
    quantity: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=STATUS_ACTIVE)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class Effect(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    """Efeito com duração em tempo do mundo (ends_at nulo = até ser removido)."""

    __tablename__ = "effects"

    target_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    definition_key: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("entities.id", ondelete="SET NULL"))
    intensity: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    ends_at: Mapped[int | None] = mapped_column(BigInteger)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
