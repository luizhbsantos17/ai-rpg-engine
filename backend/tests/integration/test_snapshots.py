"""Backups por campanha, restauração, exportação e importação (D-014; SPEC 15; Parte 22 caso 17)."""

import pytest

from app import create_app
from app.engine.operations import OperationContext, apply_operations
from app.persistence.repositories import CampaignData
from app.persistence.snapshots import list_snapshots
from tests.conftest import make_settings

PASSWORD = "senha"


@pytest.fixture
def app_(tmp_path, migrated_db_template):
    application = create_app(make_settings(tmp_path, migrated_db_template, ADMIN_PASSWORD=PASSWORD))
    yield application
    application.extensions["rpg_engine"].db.dispose()


@pytest.fixture
def client(app_):
    return app_.test_client()


def build(app_, client, title, strength):
    campaign_id = client.post("/api/campaigns", json={"title": title}).get_json()["campaign"]["id"]
    with app_.extensions["rpg_engine"].db.transaction() as session:
        data = CampaignData(session, campaign_id)
        outcomes = apply_operations(OperationContext(data, "system", 1), [
            {"op": "definition.create", "kind": "attribute", "key": "forca", "data": {"name": "Força", "value_type": "integer"}},
            {"op": "definition.create", "kind": "item", "key": "anel", "data": {"name": "Anel"}},
            {"op": "entity.create", "ref": "casa", "kind": "location", "name": "Casa"},
            {"op": "entity.create", "kind": "character", "name": "Kael", "is_player": True, "location": "casa",
             "attributes": {"forca": strength}},
            {"op": "item.create", "key": "anel", "owner": "player"},
            {"op": "canon.assert", "key": "lua", "subject": "céu", "statement": "A lua é vermelha."},
        ])
        assert all(o.status == "applied" for o in outcomes)
        data.memory_search.index("narration", "x", 1, "O anel de prata brilha na casa.")
    return campaign_id


def strength(app_, campaign_id):
    with app_.extensions["rpg_engine"].db.transaction() as session:
        data = CampaignData(session, campaign_id)
        player = data.entities.player()
        return data.attributes.get_for(player.id, "forca").value if player else None


def admin(client, campaign_id, token, command):
    return client.post(f"/api/campaigns/{campaign_id}/admin", json={"command": command},
                       headers={"X-Admin-Token": token}).get_json()


def test_restore_returns_one_campaign_in_time_without_touching_others(app_, client, settings):
    a = build(app_, client, "A", 5)
    b = build(app_, client, "B", 7)
    token = client.post("/api/admin/login", json={"password": PASSWORD}).get_json()["token"]
    created = admin(client, a, token, '/admin snapshot create "antes da luta"')
    snapshot_id = created["lines"][0].split(": ")[1]

    admin(client, a, token, "/admin set player.forca 99")
    admin(client, b, token, "/admin set player.forca 42")
    ask = admin(client, a, token, f"/admin snapshot.restore {snapshot_id}")
    done = admin(client, a, token, f"/admin snapshot.restore {snapshot_id} --confirm {ask['confirmation_code']}")
    assert done["ok"], done

    assert strength(app_, a) == "5"  # A voltou no tempo
    assert strength(app_, b) == "42"  # B não foi afetada (D-014)
    with app_.extensions["rpg_engine"].db.transaction() as session:
        data = CampaignData(session, a)
        assert [i.definition_key for i in data.items.held_by(data.entities.player().id)] == ["anel"]
        assert data.canon.current("lua").statement == "A lua é vermelha."
        assert len(data.memory_search.search("anel prata")) == 1
    labels = [s["label"] for s in list_snapshots(app_.extensions["rpg_engine"].settings.data_dir, a)]
    assert "antes-de-snapshot.restore" in labels and "antes da luta" in labels  # cópia automática antes


def test_destructive_admin_commands_make_a_safety_snapshot(app_, client):
    a = build(app_, client, "A", 5)
    token = client.post("/api/admin/login", json={"password": PASSWORD}).get_json()["token"]
    ask = admin(client, a, token, "/admin kill player")
    admin(client, a, token, f"/admin kill player --confirm {ask['confirmation_code']}")
    labels = [s["label"] for s in list_snapshots(app_.extensions["rpg_engine"].settings.data_dir, a)]
    assert labels == ["antes-de-kill"]


def test_export_delete_import_round_trip(app_, client):
    a = build(app_, client, "Viagem", 8)
    exported = client.get(f"/api/campaigns/{a}/export")
    assert exported.status_code == 200 and "attachment" in exported.headers["Content-Disposition"]
    snapshot = exported.get_json()

    assert client.post("/api/campaigns/import", json=snapshot).status_code == 400  # já existe aqui
    assert client.delete(f"/api/campaigns/{a}", json={"confirm_title": "Viagem"}).status_code == 204
    labels = [s["label"] for s in list_snapshots(app_.extensions["rpg_engine"].settings.data_dir, a)]
    assert labels == ["antes-de-excluir"]  # excluir guarda uma cópia antes

    imported = client.post("/api/campaigns/import", json=snapshot)
    assert imported.status_code == 201 and imported.get_json()["campaign"]["title"] == "Viagem"
    assert strength(app_, a) == "8"


def test_invalid_import_files(client):
    assert client.post("/api/campaigns/import", json={"format": "outra-coisa"}).status_code == 400
    assert client.post("/api/campaigns/import", json={"format": "ai-rpg-engine/campaign", "format_version": 1}).status_code == 400
    assert client.post("/api/campaigns/import", data="não é json").status_code == 400


def test_snapshot_ids_cannot_escape_the_campaign_folder(app_, client):
    a = build(app_, client, "A", 5)
    token = client.post("/api/admin/login", json={"password": PASSWORD}).get_json()["token"]
    ask = admin(client, a, token, "/admin snapshot.restore ../../segredo")
    result = admin(client, a, token, f"/admin snapshot.restore ../../segredo --confirm {ask['confirmation_code']}")
    assert not result["ok"] and "inválido" in result["lines"][0]
