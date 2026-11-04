"""Missões tradicionais e emergentes (SPEC 10.1)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base, CampaignScopedMixin, CreatedAtMixin, IdMixin
from app.persistence.types import UTCDateTime, utc_now


class Quest(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    __tablename__ = "quests"
    __table_args__ = (UniqueConstraint("campaign_id", "key"),)

    KINDS = ("main", "side", "optional", "dynamic")
    STATUSES = ("active", "completed", "failed", "abandoned")

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="side")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    giver_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("entities.id", ondelete="SET NULL"))
    # Missão oculta: existe e avança, mas o jogador não vê até ser revelada.
    hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    objectives: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)  # [{"text", "done"}]
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utc_now, onupdate=utc_now)
