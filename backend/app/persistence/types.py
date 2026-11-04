"""Tipos de coluna e utilitários compartilhados pelos modelos."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


def new_id() -> str:
    """Identificador único (UUID) em texto."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator):
    """Data/hora sempre em UTC.

    O SQLite não guarda fuso horário; este tipo grava em UTC e devolve com fuso UTC,
    para o comportamento ser igual no SQLite e no PostgreSQL.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Datas precisam ter fuso horário (use utc_now()).")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=UTC)
