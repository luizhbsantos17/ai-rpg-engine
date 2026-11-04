"""Exportação, snapshot e restauração de UMA campanha (D-014; SPEC 15, Parte 22 caso 17).

Exportar = todas as linhas das tabelas da campanha (filtradas por campaign_id) + a própria campanha,
a introdução e o índice de busca. Restaurar = apagar só aquela campanha e inserir tudo de volta, numa
transação (com as chaves estrangeiras conferidas no fim). As outras campanhas não são tocadas.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Table, delete, insert, select, text
from sqlalchemy.orm import Session

from app.persistence.models import FTS_TABLE, Base, Campaign
from app.persistence.types import UTCDateTime, utc_now

FORMAT_VERSION = 1
PLATFORM_TABLES = ("users",)  # não pertencem à campanha


class SnapshotError(ValueError):
    pass


def _campaign_tables() -> list[Table]:
    """Tabelas da campanha, pais antes dos filhos (ordem segura para inserir)."""
    return [t for t in Base.metadata.sorted_tables if t.name not in PLATFORM_TABLES and t.name != "campaigns"
            and "campaign_id" in t.columns]


def export_campaign(session: Session, campaign_id: str) -> dict[str, Any]:
    campaign_table = Campaign.__table__
    campaign_row = session.execute(select(campaign_table).where(campaign_table.c.id == campaign_id)).mappings().first()
    if campaign_row is None:
        raise SnapshotError("Campanha não encontrada.")
    tables = {"campaigns": [_to_json(campaign_table, dict(campaign_row))]}
    for table in _campaign_tables():
        rows = session.execute(select(table).where(table.c.campaign_id == campaign_id)).mappings()
        tables[table.name] = [_to_json(table, dict(row)) for row in rows]
    fts = session.execute(
        text(f"SELECT kind, ref_id, turn_number, content FROM {FTS_TABLE} WHERE campaign_id = :c"), {"c": campaign_id}
    ).mappings()
    return {
        "format": "ai-rpg-engine/campaign", "format_version": FORMAT_VERSION,
        "schema_revision": _schema_revision(session), "exported_at": utc_now().isoformat(),
        "campaign_id": campaign_id, "title": campaign_row["title"],
        "tables": tables, "memory_index": [dict(r) for r in fts],
    }


def restore_campaign(session: Session, snapshot: dict[str, Any], owner_id: str, replace_existing: bool) -> str:
    """Recoloca a campanha do snapshot. `replace_existing`: apaga a versão atual dela antes (restaurar)."""
    if snapshot.get("format") != "ai-rpg-engine/campaign":
        raise SnapshotError("Arquivo não é uma exportação de campanha do AI RPG Engine.")
    if snapshot.get("format_version") != FORMAT_VERSION:
        raise SnapshotError("Versão do arquivo de campanha não suportada.")
    if snapshot.get("schema_revision") not in (None, _schema_revision(session)):
        raise SnapshotError("O arquivo é de outra versão do banco; restaure com a mesma versão do programa.")
    campaign_id = snapshot["campaign_id"]
    campaign_table = Campaign.__table__
    exists = session.execute(select(campaign_table.c.id).where(campaign_table.c.id == campaign_id)).first()
    if exists and not replace_existing:
        raise SnapshotError("Essa campanha já existe aqui. Para voltar no tempo, use a restauração.")

    session.execute(text("PRAGMA defer_foreign_keys = ON"))  # confere as referências no fim da transação
    if exists:
        session.execute(text(f"DELETE FROM {FTS_TABLE} WHERE campaign_id = :c"), {"c": campaign_id})
        session.execute(delete(campaign_table).where(campaign_table.c.id == campaign_id))  # cascata: só esta campanha
    tables = snapshot["tables"]
    rows = [dict(r, owner_id=owner_id) for r in tables["campaigns"]]
    session.execute(insert(campaign_table), [_from_json(campaign_table, r) for r in rows])
    for table in _campaign_tables():
        records = tables.get(table.name, [])
        if records:
            session.execute(insert(table), [_from_json(table, r) for r in records])
    for entry in snapshot.get("memory_index", []):
        session.execute(
            text(f"INSERT INTO {FTS_TABLE} (campaign_id, kind, ref_id, turn_number, content) "
                 "VALUES (:c, :kind, :ref_id, :turn_number, :content)"), {"c": campaign_id, **entry})
    session.flush()
    return campaign_id


def _schema_revision(session: Session) -> str | None:
    try:
        return session.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except Exception:  # banco sem Alembic (não deve acontecer no programa)
        return None


def _to_json(table: Table, row: dict[str, Any]) -> dict[str, Any]:
    return {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in row.items()}


def _from_json(table: Table, row: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for key, value in row.items():
        if key not in table.columns:
            continue  # coluna que não existe mais nesta versão
        if isinstance(table.columns[key].type, UTCDateTime) and isinstance(value, str):
            value = datetime.fromisoformat(value)
        out[key] = value
    return out


# ---------------------------------------------------------------- arquivos de snapshot

def snapshot_dir(data_dir: Path, campaign_id: str) -> Path:
    return data_dir / "backups" / campaign_id


def write_snapshot(data_dir: Path, snapshot: dict[str, Any], label: str) -> str:
    folder = snapshot_dir(data_dir, snapshot["campaign_id"])
    folder.mkdir(parents=True, exist_ok=True)
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in label.lower())[:40].strip("-") or "manual"
    snapshot_id = f"{utc_now():%Y%m%d-%H%M%S-%f}-{safe}"
    (folder / f"{snapshot_id}.json").write_text(json.dumps({**snapshot, "label": label}, ensure_ascii=False),
                                               encoding="utf-8")
    return snapshot_id


def list_snapshots(data_dir: Path, campaign_id: str) -> list[dict[str, Any]]:
    folder = snapshot_dir(data_dir, campaign_id)
    if not folder.is_dir():
        return []
    items = []
    for path in sorted(folder.glob("*.json"), reverse=True):
        try:
            header = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        items.append({"id": path.stem, "label": header.get("label", ""), "exported_at": header.get("exported_at")})
    return items


AUTO_LABEL_PREFIX = "automatico"


def prune_automatic(data_dir: Path, campaign_id: str, keep: int) -> int:
    """Apaga snapshots AUTOMÁTICOS antigos, mantendo os `keep` mais recentes. Manuais nunca são apagados."""
    automatic = [s for s in list_snapshots(data_dir, campaign_id) if s["label"].startswith(AUTO_LABEL_PREFIX)]
    removed = 0
    for old in automatic[keep:]:
        (snapshot_dir(data_dir, campaign_id) / f"{old['id']}.json").unlink(missing_ok=True)
        removed += 1
    return removed


def read_snapshot(data_dir: Path, campaign_id: str, snapshot_id: str) -> dict[str, Any]:
    if not snapshot_id or any(ch in snapshot_id for ch in "/\\.."):
        raise SnapshotError("Identificador de snapshot inválido.")
    path = snapshot_dir(data_dir, campaign_id) / f"{snapshot_id}.json"
    if not path.is_file():
        raise SnapshotError("Snapshot não encontrado.")
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("campaign_id") != campaign_id:
        raise SnapshotError("Esse snapshot é de outra campanha.")
    return snapshot


__all__ = ["SnapshotError", "export_campaign", "list_snapshots", "read_snapshot", "restore_campaign",
           "write_snapshot"]
