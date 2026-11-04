"""Registro canônico do universo (SPEC 3.4): fatos estabelecidos, com versões.

Alterar um fato cria uma NOVA versão (`supersedes_id` aponta para a anterior); a antiga
deixa de ser a atual mas nunca é apagada. Assim o passado não é reescrito em silêncio.
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base, CampaignScopedMixin, CreatedAtMixin, IdMixin


class CanonFact(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    __tablename__ = "canon_facts"
    __table_args__ = (
        UniqueConstraint("campaign_id", "key", "version"),
        Index("ix_canon_facts_current", "campaign_id", "is_current"),
    )

    STATUS_CONFIRMED = "confirmed"
    STATUS_RUMOR = "rumor"
    STATUS_FALSE = "false"  # algo em que se acredita, mas é falso (a verdade fica com o mestre)

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=STATUS_CONFIRMED)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    supersedes_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("canon_facts.id", ondelete="SET NULL"))
    reason: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(20), nullable=False)
