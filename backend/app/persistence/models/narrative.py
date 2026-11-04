"""Turnos, mensagens e o log de eventos."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base, CampaignScopedMixin, CreatedAtMixin, IdMixin
from app.persistence.types import UTCDateTime, new_id


class Turn(CampaignScopedMixin, CreatedAtMixin, Base):
    """Uma jogada. O `id` vem do frontend e serve de chave de idempotência (ARCHITECTURE §6)."""

    __tablename__ = "turns"
    __table_args__ = (UniqueConstraint("campaign_id", "number"),)

    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    player_input: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=STATUS_PROCESSING)
    error: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class Message(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    """Texto mostrado no chat. A ordem é dada por `seq`, nunca pelo horário (D-015)."""

    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("campaign_id", "seq"),)

    ROLE_PLAYER = "player"
    ROLE_NARRATION = "narration"
    ROLE_SYSTEM = "system"

    turn_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("turns.id", ondelete="CASCADE"), index=True
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class Event(CampaignScopedMixin, CreatedAtMixin, Base):
    """Log de eventos: registro auditável e permanente do que aconteceu (SPEC 15.2)."""

    __tablename__ = "events"
    __table_args__ = (Index("ix_events_campaign_seq", "campaign_id", "seq"),)

    SOURCE_AI = "ai"
    SOURCE_ENGINE = "engine"
    SOURCE_ADMIN = "admin"
    SOURCE_SYSTEM = "system"

    # seq: ordem global de gravação (inteiro automático). id: identificador estável para exportar.
    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, default=new_id)
    turn_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("turns.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    world_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
