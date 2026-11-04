"""Modo administrador e debug (SPEC 16; Parte 22 casos 16 e 25)."""

import uuid

import pytest

from app import create_app
from app.admin import is_admin_command
from app.admin.parser import CommandSyntaxError, parse_command
from app.admin.sessions import AdminAccessError, AdminSessions
from app.engine.operations import OperationContext, apply_operations
from app.persistence.repositories import CampaignData
from tests.conftest import make_settings

PASSWORD = "senha-de-teste"
WORLD = [
    {"op": "definition.create", "kind": "attribute", "key": "forca", "data": {"name": "Força", "value_type": "integer"}},
    {"op": "definition.create", "kind": "attribute", "key": "vida", "data": {"name": "Vida", "value_type": "integer", "resource": True}},
    {"op": "definition.create", "kind": "skill", "key": "voo", "data": {"name": "Voo"}},
    {"op": "definition.create", "kind": "item", "key": "pocao", "data": {"name": "Poção"}},
    {"op": "entity.create", "ref": "vila", "kind": "location", "name": "Vila"},
    {"op": "entity.create", "ref": "torre", "kind": "location", "name": "Torre Negra"},
    {"op": "entity.create", "kind": "character", "name": "Kael", "is_player": True, "location": "vila",
     "attributes": {"forca": 5, "vida": {"value": 10, "max": 20}}},
    {"op": "entity.create", "kind": "character", "name": "Ana Clara", "location": "vila", "attributes": {"forca": 3}},
]


@pytest.fixture
def app_(tmp_path, migrated_db_template):
    application = create_app(make_settings(tmp_path, migrated_db_template, ADMIN_PASSWORD=PASSWORD))
    yield application
    application.extensions["rpg_engine"].db.dispose()


@pytest.fixture
def client(app_):
    return app_.test_client()


@pytest.fixture
def campaign_id(app_, client):
    campaign_id = client.post("/api/campaigns", json={"title": "Admin"}).get_json()["campaign"]["id"]
    services = app_.extensions["rpg_engine"]
    with services.db.transaction() as session:
        outcomes = apply_operations(OperationContext(CampaignData(session, campaign_id), "system", 1), WORLD)
        assert all(o.status == "applied" for o in outcomes)
    return campaign_id


@pytest.fixture
def token(client):
    return client.post("/api/admin/login", json={"password": PASSWORD}).get_json()["token"]


def run(client, campaign_id, token, command):
    response = client.post(f"/api/campaigns/{campaign_id}/admin", json={"command": command},
                           headers={"X-Admin-Token": token})
    return response.status_code, response.get_json()


def read(app_, campaign_id, fn):
    with app_.extensions["rpg_engine"].db.transaction() as session:
        return fn(CampaignData(session, campaign_id))


# ---------- sintaxe e acesso

def test_only_messages_starting_with_prefix_are_commands():
    assert is_admin_command("/admin help") and is_admin_command("  /debug show_events")
    assert not is_admin_command("Eu grito /admin para o céu") and not is_admin_command("/administrar")


def test_parser():
    command = parse_command('/admin give npc "Ana Clara" item pocao --qty 3')
    assert (command.group, command.verb, command.args, command.options) == (
        "admin", "give", ["npc", "Ana Clara", "item", "pocao"], {"qty": "3"})
    with pytest.raises(CommandSyntaxError):
        parse_command('/admin give npc "sem fechar')
    with pytest.raises(CommandSyntaxError):
        parse_command("/admin set x --qty")


def test_access_requires_password_and_session(client, campaign_id):
    assert client.post("/api/admin/login", json={"password": "errada"}).status_code == 403
    status, body = run(client, campaign_id, "token-falso", "/admin help")
    assert status == 401 and "Sessão" in body["error"]["message"]


def test_admin_disabled_without_password():
    with pytest.raises(AdminAccessError, match="ADMIN_PASSWORD"):
        AdminSessions(None).login("qualquer")


def test_sessions_expire():
    now = [1000.0]
    sessions = AdminSessions("x", clock=lambda: now[0])
    token = sessions.login("x")
    sessions.check(token)
    now[0] += 31 * 60
    with pytest.raises(AdminAccessError):
        sessions.check(token)


def test_commands_never_reach_the_ai_through_the_story(app_, client, campaign_id):
    response = client.post(f"/api/campaigns/{campaign_id}/turns",
                           json={"turn_id": str(uuid.uuid4()), "input": "/admin set player.forca 99"})
    assert response.status_code == 400 and "modo administrador" in response.get_json()["error"]["message"]
    assert app_.extensions["rpg_engine"].provider.calls == []
    assert read(app_, campaign_id, lambda d: d.turns.count()) == 0


# ---------- consultas

def test_help_and_status(client, campaign_id, token):
    _, body = run(client, campaign_id, token, "/admin help")
    assert body["ok"] and any("/admin set" in line for line in body["lines"])
    _, body = run(client, campaign_id, token, '/admin status npc "Ana Clara"')
    assert body["ok"] and "forca=3" in body["lines"][2]
    _, body = run(client, campaign_id, token, "/admin nada")
    assert not body["ok"] and "desconhecido" in body["lines"][0]


def test_debug_commands(client, campaign_id, token):
    for command in ("/debug show_events --last 5", "/debug inspect_rules attribute", '/debug inspect_entity "Ana Clara"',
                    "/debug inspect_ai_requests", "/debug show_memory", "/debug validate_world"):
        _, body = run(client, campaign_id, token, command)
        assert body["ok"], (command, body)
    _, body = run(client, campaign_id, token, "/debug validate_world")
    assert body["lines"] == ["Nenhuma inconsistência encontrada."]


# ---------- alterações (pelo pipeline do motor, com origem admin)

def test_set_give_teleport_create_go_through_engine_and_audit(app_, client, campaign_id, token):
    assert run(client, campaign_id, token, "/admin set player.forca 20")[1]["ok"]
    assert run(client, campaign_id, token, "/admin set player.vida 15/30")[1]["ok"]
    assert run(client, campaign_id, token, "/admin give player skill Voo --level 3")[1]["ok"]
    assert run(client, campaign_id, token, "/admin give player item pocao --qty 2")[1]["ok"]
    assert run(client, campaign_id, token, '/admin teleport player "Torre Negra"')[1]["ok"]
    assert run(client, campaign_id, token, '/admin create npc "Guarda" --desc "sonolento"')[1]["ok"]
    _, rejected = run(client, campaign_id, token, "/admin set player.forca 2.5")
    assert not rejected["ok"] and "inteiros" in rejected["lines"][0]  # o motor valida também o admin

    def state(d):
        player = d.entities.player()
        return ({a.definition_key: (a.value, a.max_value) for a in d.attributes.for_entity(player.id)},
                [(s.definition_key, s.level) for s in d.skills.for_entity(player.id)],
                d.entities.get(player.location_id).name,
                [e.source for e in d.events.list_ordered() if e.type == "attribute.set"],
                len(d.admin_audit.latest(50)))

    attributes, skills, location, sources, audits = read(app_, campaign_id, state)
    assert attributes == {"forca": ("20", None), "vida": ("15", "30")}
    assert skills == [("voo", 3)] and location == "Torre Negra"
    assert set(sources) == {"admin"}  # alterações feitas pelo comando ficam com origem "admin"
    assert audits == 6  # comandos que falharam não ficam registrados como executados


def test_undo_reverses_last_reversible_command(app_, client, campaign_id, token):
    run(client, campaign_id, token, "/admin set player.forca 50")
    run(client, campaign_id, token, '/admin teleport player "Torre Negra"')
    assert run(client, campaign_id, token, "/admin undo")[1]["lines"][0].startswith("Desfeito: /admin teleport")
    assert run(client, campaign_id, token, "/admin undo")[1]["ok"]
    location, forca = read(app_, campaign_id, lambda d: (d.entities.get(d.entities.player().location_id).name,
                                                       d.attributes.get_for(d.entities.player().id, "forca").value))
    assert (location, forca) == ("Vila", "5")
    assert not run(client, campaign_id, token, "/admin undo")[1]["ok"]  # nada mais para desfazer


def test_destructive_commands_require_confirmation_code(app_, client, campaign_id, token):
    _, first = run(client, campaign_id, token, '/admin kill npc "Ana Clara"')
    assert not first["ok"] and first["confirmation_code"]
    assert read(app_, campaign_id, lambda d: next(e for e in d.entities.list() if e.name == "Ana Clara").status) == "active"
    _, wrong = run(client, campaign_id, token, '/admin kill npc "Ana Clara" --confirm ZZZZ')
    assert not wrong["ok"]
    _, again = run(client, campaign_id, token, '/admin kill npc "Ana Clara"')
    _, done = run(client, campaign_id, token, f'/admin kill npc "Ana Clara" --confirm {again["confirmation_code"]}')
    assert done["ok"]
    assert read(app_, campaign_id, lambda d: next(e for e in d.entities.list() if e.name == "Ana Clara").status) == "dead"


def test_code_only_confirms_the_same_command(client, campaign_id, token):
    _, first = run(client, campaign_id, token, '/admin kill npc "Ana Clara"')
    _, other = run(client, campaign_id, token, f'/admin kill player --confirm {first["confirmation_code"]}')
    assert not other["ok"] and other["confirmation_code"]


def test_world_time_and_ambiguous_names(app_, client, campaign_id, token):
    _, ask = run(client, campaign_id, token, "/admin world.time advance 2d")
    _, done = run(client, campaign_id, token, f"/admin world.time advance 2d --confirm {ask['confirmation_code']}")
    assert done["ok"] and "dia 3, 00:00" in done["lines"][0]
    run(client, campaign_id, token, '/admin create npc "Ana Clara"')
    _, ambiguous = run(client, campaign_id, token, '/admin status "Ana Clara"')
    assert not ambiguous["ok"] and "mais de um" in ambiguous["lines"][0]


def test_admin_cannot_touch_other_campaigns(client, campaign_id, token):
    other = client.post("/api/campaigns", json={"title": "Outra"}).get_json()["campaign"]["id"]
    _, body = run(client, other, token, '/admin status npc "Ana Clara"')
    assert not body["ok"]  # Ana Clara é de outra campanha
