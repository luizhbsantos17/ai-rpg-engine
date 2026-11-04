"""Base dos modelos e colunas comuns."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, MetaData, String
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from app.persistence.types import UTCDateTime, new_id, utc_now

# Nomes previsíveis para índices e restrições: o Alembic precisa deles para alterar
# tabelas no SQLite e para gerar migrações estáveis.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class IdMixin:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False)


class CampaignScopedMixin:
    """Toda tabela de dados de jogo pertence a uma campanha (isolamento entre campanhas).

    Apagar a campanha apaga junto as linhas dela (ON DELETE CASCADE).
    """

    @declared_attr
    def campaign_id(cls) -> Mapped[str]:
        return mapped_column(
            String(36),
            ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
