"""Snapshots e exportações de versões anteriores do programa continuam restauráveis (D-050)."""

import uuid

from alembic import command
from sqlalchemy import MetaData, create_engine

from app.persistence.migrations import alembic_config
from app.persistence.repositories import CampaignData
from app.persistence.snapshots import list_snapshots, write_snapshot
from tests.integration.test_snapshots import PASSWORD, admin, app_, build, client, strength  # noqa: F401

ETAPA2 = "f2dd50ffa852"  # antes de: mecânicas no turno, cânone, conhecimento, missões, resumos...


def as_old_version(snapshot, revision, tmp_path):
    """O que a versão antiga teria exportado: só as tabelas e colunas que existiam nela."""
    url = "sqlite:///" + (tmp_path / f"esquema-{revision}.db").as_posix()
    command.upgrade(alembic_config(url), revision)
    engine = create_engine(url)
    metadata = MetaData()
    metadata.reflect(engine)
    engine.dispose()
    tables = {name: [{k: v for k, v in row.items() if k in metadata.tables[name].columns} for row in rows]
              for name, rows in snapshot["tables"].items() if name in metadata.tables}
    return {**snapshot, "schema_revision": revision, "tables": tables}


def play_one_turn(app_, campaign_id):
    services = app_.extensions["rpg_engine"]
    services.provider.queue("O vento sopra na casa.")
    prepared = services.turns.prepare(services.local_user_id, campaign_id, str(uuid.uuid4()), "Olho em volta.")
    list(services.turns.run(prepared))


def test_import_file_from_older_version(app_, client, tmp_path):
    campaign_id = build(app_, client, "Antiga", 7)
    play_one_turn(app_, campaign_id)
    old = as_old_version(client.get(f"/api/campaigns/{campaign_id}/export").get_json(), ETAPA2, tmp_path)
    assert "canon_facts" not in old["tables"] and "mechanics" not in old["tables"]["turns"][0]
    assert client.delete(f"/api/campaigns/{campaign_id}", json={"confirm_title": "Antiga"}).status_code == 204

    imported = client.post("/api/campaigns/import", json=old)
    assert imported.status_code == 201, imported.get_json()
    assert strength(app_, campaign_id) == "7"
    history = client.get(f"/api/campaigns/{campaign_id}/history").get_json()
    assert [t["status"] for t in history["turns"]] == ["completed"]
    assert any("vento" in m["content"] for m in history["messages"])
    with app_.extensions["rpg_engine"].db.transaction() as session:
        data = CampaignData(session, campaign_id)
        assert [i.definition_key for i in data.items.held_by(data.entities.player().id)] == ["anel"]
        assert data.canon.list_current(10) == []  # não existia naquela versão
        assert data.memory_search.search("anel")  # o índice de busca veio junto
    assert not any((app_.extensions["rpg_engine"].settings.data_dir / "tmp").glob("*"))  # banco temporário apagado


def test_admin_restore_of_older_snapshot(app_, client, tmp_path):
    campaign_id = build(app_, client, "Volta", 3)
    data_dir = app_.extensions["rpg_engine"].settings.data_dir
    old = as_old_version(client.get(f"/api/campaigns/{campaign_id}/export").get_json(), ETAPA2, tmp_path)
    snapshot_id = write_snapshot(data_dir, old, "de-uma-versao-antiga")
    with app_.extensions["rpg_engine"].db.transaction() as session:
        data = CampaignData(session, campaign_id)
        data.attributes.get_for(data.entities.player().id, "forca").value = "99"

    token = client.post("/api/admin/login", json={"password": PASSWORD}).get_json()["token"]
    first = admin(client, campaign_id, token, f"/admin snapshot.restore {snapshot_id}")
    code = first["confirmation_code"]
    done = admin(client, campaign_id, token, f"/admin snapshot.restore {snapshot_id} --confirm {code}")
    assert "restaurada" in done["lines"][0], done
    assert strength(app_, campaign_id) == "3"
    assert any(s["label"].startswith("antes-de") for s in list_snapshots(data_dir, campaign_id))


def test_file_from_newer_or_unknown_version_is_refused(app_, client):
    campaign_id = build(app_, client, "Futuro", 5)
    snapshot = client.get(f"/api/campaigns/{campaign_id}/export").get_json()
    client.delete(f"/api/campaigns/{campaign_id}", json={"confirm_title": "Futuro"})
    response = client.post("/api/campaigns/import", json={**snapshot, "schema_revision": "ffffffffffff"})
    assert response.status_code == 400
    assert "versão mais nova" in response.get_json()["error"]["message"]
