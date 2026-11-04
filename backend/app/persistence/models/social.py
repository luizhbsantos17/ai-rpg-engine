"""Relacionamentos (SPEC 9): direcionais, com várias dimensões e histórico de causas.

A relação de A com B é diferente da de B com A. As dimensões são livres (confiança, afeto,
medo, respeito, ciúme...) e toda mudança fica registrada com o acontecimento que a causou,
para a evolução depender da história, não de uma barra numérica solta.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base, CampaignScopedMixin, CreatedAtMixin, IdMixin
from app.persistence.types import UTCDateTime, utc_now


class Relationship(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    __tablename__ = "relationships"
    __table_args__ = (UniqueConstraint("source_id", "target_id"),)

    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    dimensions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)  # {"confianca": 20}
    labels: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)  # ["amigo de infância"]
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utc_now, onupdate=utc_now)


class RelationshipEvent(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    __tablename__ = "relationship_events"

    relationship_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("relationships.id", ondelete="CASCADE"), nullable=False, index=True
    )
    turn_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("turns.id", ondelete="SET NULL"))
    changes: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    cause: Mapped[str] = mapped_column(Text, nullable=False)
    world_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
