"""Configurações por campanha, versionadas (SPEC 19): cada mudança é uma versão nova; nada é sobrescrito."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base, CampaignScopedMixin, CreatedAtMixin, IdMixin


class CampaignSetting(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    __tablename__ = "campaign_settings"
    __table_args__ = (UniqueConstraint("campaign_id", "kind", "version"),)

    KIND_EXPERIENCE = "experience"  # como o jogo é apresentado/executado
    KIND_CONTENT = "content"  # maturidade por categoria (SPEC 14)

    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
