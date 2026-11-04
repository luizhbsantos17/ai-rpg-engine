"""Acontecimentos agendados no relógio do mundo (SPEC 10.2)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base, CampaignScopedMixin, CreatedAtMixin, IdMixin


class ScheduledEvent(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    """Acontece quando o relógio do mundo chegar em `due_at`; pode aplicar operações nesse momento."""

    __tablename__ = "scheduled_events"
    __table_args__ = (Index("ix_scheduled_events_due", "campaign_id", "status", "due_at"),)

    STATUS_PENDING = "pending"
    STATUS_DONE = "done"

    due_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    operations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=STATUS_PENDING)
    turn_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("turns.id", ondelete="SET NULL"))
