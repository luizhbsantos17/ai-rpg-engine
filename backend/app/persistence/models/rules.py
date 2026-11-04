"""Definições: o "sistema de RPG" de cada campanha (ARCHITECTURE §5.1, D-004).

Definições são ABERTAS: a IA cria atributos, habilidades, itens, regras de teste... com
propriedades livres em `data`. Alterar uma definição cria uma NOVA versão que aponta para
a anterior (`supersedes_id`); a antiga nunca é apagada (SPEC 3.4 e 19).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base, CampaignScopedMixin, CreatedAtMixin, IdMixin


class Definition(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    __tablename__ = "definitions"
    __table_args__ = (
        UniqueConstraint("campaign_id", "kind", "key", "version"),
        Index("ix_definitions_current", "campaign_id", "kind", "key", "is_current"),
    )

    kind: Mapped[str] = mapped_column(String(40), nullable=False)  # attribute, skill, item, check_rule...
    key: Mapped[str] = mapped_column(String(100), nullable=False)  # identificador estável: "forca"
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    supersedes_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("definitions.id", ondelete="SET NULL"))
    created_by: Mapped[str] = mapped_column(String(20), nullable=False)  # ai | admin | system
