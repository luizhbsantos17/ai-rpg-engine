"""Conexão com o banco, sessões e transações.

- SQLite em modo WAL (mais resistente a corrupção se o programa fechar de repente).
- Chaves estrangeiras ligadas (o SQLite vem com elas desligadas).
- `Database.transaction()` abre uma transação curta: tudo é gravado junto no fim,
  ou nada é gravado se acontecer um erro (D-012: nunca chamar a IA dentro dela).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

SQLITE_BUSY_TIMEOUT_MS = 10_000


def create_db_engine(database_url: str) -> Engine:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite":
        return create_engine(url, pool_pre_ping=True)

    if url.database and url.database != ":memory:":
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"timeout": SQLITE_BUSY_TIMEOUT_MS / 1000})

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
        cursor.close()

    return engine


class Database:
    """Ponto único de acesso ao banco da aplicação."""

    def __init__(self, database_url: str):
        self.url = database_url
        self.engine = create_db_engine(database_url)
        self._sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

    @contextmanager
    def transaction(self) -> Iterator[Session]:
        """Abre uma sessão com transação; confirma no fim ou desfaz tudo se der erro."""
        session = self._sessions()
        try:
            with session.begin():
                yield session
        finally:
            session.close()

    def dispose(self) -> None:
        """Fecha todas as conexões (usado ao desligar e nos testes de reinício)."""
        self.engine.dispose()
