"""Configurações durante a campanha (SPEC 19 e 14; RF-23/24)."""

import json
import uuid

import pytest

from app import create_app
from app.persistence.repositories import CampaignData
from tests.conftest import make_settings

SETUP = json.dumps({"attributes": [{"name": "Vida", "resource": True, "initial_value": 10}],
                    "protagonist": {"name": "Kael"}, "starting_location": "Vila"})
CHECK = json.dumps({"intent": "x", "operations": [
    {"op": "check.request", "actor": "player", "label": "Escalar", "difficulty": 5},
    {"op": "definition.create", "kind": "skill", "key": "olhar", "data": {"name": "Olhar"}},
    {"op": "skill.grant", "entity": "player", "key": "olhar"},
]})


@pytest.fixture
def app_(tmp_path, migrated_db_template):
    application = create_app(make_settings(tmp_path, migrated_db_template, AI_MECHANICS="true"))
    yield application
    application.extensions["rpg_engine"].db.dispose()


@pytest.fixture
def client(app_):
    return app_.test_client()


@pytest.fixture
def fake(app_):
    return app_.extensions["rpg_engine"].provider


@pytest.fixture
def campaign_id(client):
    return client.post("/api/campaigns", json={"title": "Config"}).get_json()["campaign"]["id"]


def play(client, campaign_id, text="Ajo."):
    response = client.post(f"/api/campaigns/{campaign_id}/turns", json={"turn_id": str(uuid.uuid4()), "input": text})
    return response.get_data(as_text=True)


def test_defaults_and_rules_listing(client, campaign_id):
    view = client.get(f"/api/campaigns/{campaign_id}/settings").get_json()
    assert view["experience"]["show_dice"] is True and view["experience"]["mechanics"] is None
    assert view["content"]["intensity"] == 2 and "sexual" in view["content_categories"]
    assert view["provider"]["name"] == "fake" and view["rules"] == []


def test_changes_are_versioned_and_logged(app_, client, campaign_id):
    url = f"/api/campaigns/{campaign_id}/settings"
    first = client.put(url, json={"experience": {"creativity": 1.2}}).get_json()
    second = client.put(url, json={"experience": {"creativity": 0.4, "mechanics": False}}).get_json()
    assert first["versions"]["experience"] == 1 and second["versions"]["experience"] == 2
    assert any("motor de regras" in w for w in second["warnings"])
    with app_.extensions["rpg_engine"].db.transaction() as session:
        data = CampaignData(session, campaign_id)
        assert [h.data["creativity"] for h in data.settings.history("experience")] == [1.2, 0.4]
        assert [e.type for e in data.events.list_ordered()].count("settings.changed") == 2


def test_invalid_settings_are_rejected(client, campaign_id):
    url = f"/api/campaigns/{campaign_id}/settings"
    assert client.put(url, json={"experience": {"creativity": 9}}).status_code == 400
    assert client.put(url, json={"content": {"categories": {"inexistente": 1}}}).status_code == 400
    assert client.put(url, json={"experience": {"hack": True}}).status_code == 400


def test_creativity_and_content_limits_reach_the_ai(client, fake, campaign_id):
    client.put(f"/api/campaigns/{campaign_id}/settings", json={
        "experience": {"creativity": 1.5}, "content": {"intensity": 1, "categories": {"horror": 3, "sexual": 0}},
    })
    fake.queue(SETUP, json.dumps({"intent": "x", "operations": []}), "Narração.")
    play(client, campaign_id)
    narrator = fake.calls[-1]
    assert narrator.options.temperature == 1.5
    system = narrator.messages[0].content
    assert "Horror: intenso" in system and "violencia" not in system  # nomes legíveis, não chaves
    assert "Violência: leve" in system and "Conteúdo sexual adulto: evitar" in system
    assert "só entre personagens adultos" in system  # regra fixa de segurança


def test_turning_mechanics_off_makes_a_single_ai_call(client, fake, campaign_id):
    client.put(f"/api/campaigns/{campaign_id}/settings", json={"experience": {"mechanics": False}})
    fake.queue("Só narração.")
    assert "event: done" in play(client, campaign_id)
    assert len(fake.calls) == 1


def test_system_window_can_have_another_name_in_this_universe(app_, client, fake, campaign_id):
    assert client.put(f"/api/campaigns/{campaign_id}/settings",
                      json={"experience": {"system_label": "oráculo"}}).status_code == 400  # só maiúsculas
    client.put(f"/api/campaigns/{campaign_id}/settings", json={"experience": {"system_label": "ORÁCULO"}})
    fake.queue(SETUP, CHECK, "Narração.")
    play(client, campaign_id)
    with app_.extensions["rpg_engine"].db.transaction() as session:
        notices = [m.content for m in CampaignData(session, campaign_id).messages.list_ordered() if m.role == "system"]
    assert "[ORÁCULO] Personagem criado: Kael." in notices
    assert any(n.startswith("[TESTE]") for n in notices)  # outras etiquetas não mudam


def test_presentation_preferences_hide_dice_and_system_notices(app_, client, fake, campaign_id):
    client.put(f"/api/campaigns/{campaign_id}/settings",
               json={"experience": {"show_dice": False, "system_window": False}})
    fake.queue(SETUP, CHECK, "Narração.")
    play(client, campaign_id)
    with app_.extensions["rpg_engine"].db.transaction() as session:
        data = CampaignData(session, campaign_id)
        notices = [m.content for m in data.messages.list_ordered() if m.role == "system"]
        assert notices == []  # nem [TESTE] nem [SISTEMA]
        assert data.dice_rolls.count() == 1  # mas o motor rolou e registrou normalmente
    assert "Teste 'Escalar'" in fake.calls[-1].messages[-1].content  # e o narrador sabe o resultado
