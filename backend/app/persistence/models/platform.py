"""Tabelas da plataforma: usuários e campanhas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.persistence.models.base import Base, CreatedAtMixin, IdMixin
from app.persistence.types import UTCDateTime, utc_now


class User(IdMixin, CreatedAtMixin, Base):
    """Na v1 existe um usuário local; a tabela prepara multiplayer/hospedagem (SPEC 18.4)."""

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100), nullable=False)


class Campaign(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "campaigns"

    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    genre_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # Relógio do mundo em minutos desde o início da campanha (só avança por time.advance).
    world_clock: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    # Semente base da aleatoriedade da campanha (engine/dice), registrada para auditoria.
    rng_seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    intro: Mapped[CampaignIntro] = relationship(
        back_populates="campaign", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )


class CampaignIntro(Base):
    """Separa o que o jogador vê (player_visible) dos segredos usados pela IA (gm_secret)."""

    __tablename__ = "campaign_intro"

    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), primary_key=True
    )
    player_visible: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    gm_secret: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    campaign: Mapped[Campaign] = relationship(back_populates="intro")
