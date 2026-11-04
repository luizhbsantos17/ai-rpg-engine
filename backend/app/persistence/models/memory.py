"""Memória narrativa: resumos de trechos da campanha (SPEC 15.1).

A busca por texto (memória histórica) usa uma tabela virtual FTS5 do SQLite, `memory_fts`,
criada na migração e acessada só por `MemorySearchRepository` (fora do ORM).
"""

from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base, CampaignScopedMixin, CreatedAtMixin, IdMixin

FTS_TABLE = "memory_fts"


class Summary(IdMixin, CampaignScopedMixin, CreatedAtMixin, Base):
    __tablename__ = "summaries"

    scope: Mapped[str] = mapped_column(String(20), nullable=False, default="scene")
    from_turn: Mapped[int] = mapped_column(Integer, nullable=False)
    to_turn: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
