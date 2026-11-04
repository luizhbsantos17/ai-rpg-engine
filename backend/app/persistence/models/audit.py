"""Auditoria das chamadas à IA."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base, CampaignScopedMixin, CreatedAtMixin, IdMixin


class AiRequest(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    """Cada chamada a um provedor de IA: modelo, tokens, custo estimado, duração e erro."""

    __tablename__ = "ai_requests"

    turn_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("turns.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
    # Decimal em texto; nulo quando o custo não é conhecido (nunca inventado).
    cost_estimate: Mapped[str | None] = mapped_column(String(40))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    # Mensagens enviadas à IA (para /debug show_context).
    request_messages: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
