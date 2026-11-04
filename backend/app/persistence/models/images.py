"""Imagens geradas, associadas a entidades e campanhas (SPEC 13)."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base, CampaignScopedMixin, CreatedAtMixin, IdMixin


class GeneratedImageRecord(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    __tablename__ = "images"
    # Mesmo pedido de imagem na mesma campanha = mesma imagem (evita gerar repetido, SPEC 13).
    __table_args__ = (UniqueConstraint("campaign_id", "prompt_hash"),)

    entity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("entities.id", ondelete="SET NULL"), index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_name: Mapped[str] = mapped_column(String(200), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
