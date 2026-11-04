"""Atualiza um snapshot feito numa versão anterior do programa (D-050).

Como: cria um banco temporário NA VERSÃO do arquivo, insere os dados dele, roda as migrações até a
versão atual (as mesmas que atualizam o banco do jogador, inclusive as que transformam dados) e exporta
de novo. O banco do jogo não é tocado aqui; a restauração normal acontece depois, com o arquivo atualizado.
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import DateTime, MetaData, Table, create_engine, insert

from app.persistence.db import Database
from app.persistence.migrations import alembic_config

PLACEHOLDER_OWNER_NAME = "dono do arquivo importado"  # só existe no banco temporário


class SnapshotUpgradeError(ValueError):
    pass


def known_revisions() -> set[str]:
    script = ScriptDirectory.from_config(alembic_config("sqlite://"))
    return {revision.revision for revision in script.walk_revisions()}


def upgrade_snapshot(snapshot: dict[str, Any], work_dir: Path | None = None) -> dict[str, Any]:
    """Devolve o snapshot convertido para a versão mais recente do banco."""
    from app.persistence.snapshots import export_campaign  # evita importação circular

    revision = snapshot.get("schema_revision")
    if revision not in known_revisions():
        raise SnapshotUpgradeError("O arquivo é de uma versão mais nova (ou desconhecida) do programa. "
                                   "Atualize o programa para abri-lo.")
    if work_dir is not None:
        work_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=work_dir, prefix="atualizar-snapshot-", ignore_cleanup_errors=True) as tmp:
        url = "sqlite:///" + (Path(tmp) / "antigo.db").as_posix()
        command.upgrade(alembic_config(url), revision)
        _insert_rows(url, snapshot)
        command.upgrade(alembic_config(url), "head")
        database = Database(url)
        try:
            with database.transaction() as session:
                upgraded = export_campaign(session, snapshot["campaign_id"])
        finally:
            database.dispose()
    # O índice de busca não depende do esquema das tabelas: segue igual.
    upgraded["memory_index"] = snapshot.get("memory_index", [])
    upgraded["upgraded_from"] = revision
    return upgraded


def _insert_rows(url: str, snapshot: dict[str, Any]) -> None:
    """Insere as linhas do arquivo usando o esquema ANTIGO (lido do próprio banco temporário)."""
    engine = create_engine(url)
    try:
        metadata = MetaData()
        metadata.reflect(engine)
        tables = snapshot.get("tables", {})
        with engine.begin() as connection:
            owners = {row.get("owner_id") for row in tables.get("campaigns", [])} - {None}
            if "users" in metadata.tables and owners:  # a campanha aponta para um dono; ele precisa existir
                connection.execute(insert(metadata.tables["users"]), [
                    _coerce(metadata.tables["users"], {"id": owner, "name": PLACEHOLDER_OWNER_NAME,
                                                       "created_at": datetime.now(UTC).isoformat()})
                    for owner in owners])
            for name, rows in tables.items():
                table = metadata.tables.get(name)
                if table is not None and rows:
                    connection.execute(insert(table), [_coerce(table, row) for row in rows])
    finally:
        engine.dispose()


def _coerce(table: Table, row: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for key, value in row.items():
        if key not in table.columns:
            continue
        if isinstance(table.columns[key].type, DateTime) and isinstance(value, str):
            parsed = datetime.fromisoformat(value)
            value = parsed.astimezone(UTC).replace(tzinfo=None) if parsed.tzinfo else parsed
        out[key] = value
    return out
