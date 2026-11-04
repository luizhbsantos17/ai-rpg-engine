"""Auditoria das chamadas à IA."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, BigInteger, Boolean, ForeignKey, Integer, String, Text
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


class AdminAudit(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    """Todo comando administrativo executado (SPEC 16.3), com o que é preciso para desfazer."""

    __tablename__ = "admin_audit"

    command: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[str] = mapped_column(Text, nullable=False)
    changed_state: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    undo_operations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON(none_as_null=True))  # operações inversas
    undone: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class DiceRollRecord(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    """Toda rolagem do motor, com a semente: permite auditar e reproduzir (SPEC 7.2, D-005)."""

    __tablename__ = "dice_rolls"

    turn_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("turns.id", ondelete="CASCADE"), index=True
    )
    expression: Mapped[str] = mapped_column(String(200), nullable=False)
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    result: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Detalhes: dados individuais, propósito do teste, quem rolou, dificuldade...
    context: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
