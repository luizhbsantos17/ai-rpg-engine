"""Conhecimento por observador e memória individual de NPCs (SPEC 6.5, 8.2).

Uma informação existir no mundo não significa que todos a conheçam: cada observador tem a
SUA versão (nível + origem). A memória de um NPC é dele, separada do histórico geral.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base, CampaignScopedMixin, CreatedAtMixin, IdMixin
from app.persistence.types import UTCDateTime, utc_now


class Knowledge(IdMixin, CampaignScopedMixin, Base):
    __tablename__ = "knowledge"
    __table_args__ = (UniqueConstraint("observer_id", "subject", "field"),)

    LEVELS = ("unknown", "estimated", "partial", "confirmed", "false")
    SOURCES = ("presenciou", "ouviu", "descobriu", "contaram", "deduziu", "avaliou", "ja_sabia")

    observer_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    # Sobre quem/o quê: id de uma entidade ou um tema livre ("mundo", "mapa_perdido").
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    field: Mapped[str] = mapped_column(String(100), nullable=False)  # "forca", "identidade", "segredo"...
    known_value: Mapped[str | None] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utc_now, onupdate=utc_now)


class Disguise(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    """Ocultação/falsificação de uma informação de uma entidade (SPEC 6.3).

    `field`: chave de atributo, "skills", "identity" ou "*" (tudo). `presented_value` nulo = só esconde;
    preenchido = mostra um valor FALSO. `power` é a força da ocultação contra avaliações.
    """

    __tablename__ = "disguises"
    __table_args__ = (UniqueConstraint("entity_id", "field"),)

    entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    presented_value: Mapped[str | None] = mapped_column(Text)
    power: Mapped[str] = mapped_column(String(100), nullable=False, default="0")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class NpcMemory(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    __tablename__ = "npc_memories"
    # Testemunhas ganham lembranças a cada turno: a busca "mais importantes e recentes" usa este índice.
    __table_args__ = (Index("ix_npc_memories_recall", "campaign_id", "npc_id", "importance", "created_at"),)

    npc_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("turns.id", ondelete="SET NULL"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1 (banal) a 5 (marcante)
    world_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
