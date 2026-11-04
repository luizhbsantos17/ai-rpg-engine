"""Memória em camadas (SPEC 15.1): resumos a cada N turnos e busca por palavras no passado."""

import uuid

import pytest

from app import create_app
from app.persistence.repositories import CampaignData
from app.persistence.repositories.memory import search_terms
from tests.conftest import make_settings


@pytest.fixture
def app_every_3(tmp_path, migrated_db_template):
    application = create_app(make_settings(tmp_path, migrated_db_template, AI_SUMMARY_EVERY="3"))
    yield application
    application.extensions["rpg_engine"].db.dispose()


def play(services, campaign_id, text):
    prepared = services.turns.prepare(services.local_user_id, campaign_id, str(uuid.uuid4()), text)
    return list(services.turns.run(prepared))


def test_search_terms_ignore_short_and_common_words():
    assert search_terms("Eu pergunto para Oren sobre o farol abandonado") == ["oren", "farol", "abandonado"]


def test_old_narration_is_found_by_keywords_and_reaches_the_ai(app_every_3):
    services = app_every_3.extensions["rpg_engine"]
    fake = services.provider
    campaign = services.campaigns.create(services.local_user_id, "Memória", None, [])
    fake.queue("Você encontra uma chave de bronze com o símbolo de uma serpente.", "Narração 2.", "Narração 3.",
               "RESUMO: Kael achou uma chave de bronze com uma serpente.")
    play(services, campaign["id"], "Procuro algo no baú do sótão.")
    play(services, campaign["id"], "Desço as escadas.")
    play(services, campaign["id"], "Saio para a rua.")
    # O 4º item roteirizado foi consumido pelo resumidor (a cada 3 turnos).
    with services.db.transaction() as session:
        data = CampaignData(session, campaign["id"])
        summaries = [(s.from_turn, s.to_turn, s.content) for s in data.summaries.latest(5)]
        hits = data.memory_search.search("Uso a chave de bronze na porta", limit=5)
    assert summaries == [(1, 3, "RESUMO: Kael achou uma chave de bronze com uma serpente.")]
    assert {h.kind for h in hits} == {"narration", "summary"}

    for n in range(4, 11):
        fake.queue(f"Narração {n}.")
        if n in (6, 9):
            fake.queue(f"RESUMO dos turnos até {n}.")
        play(services, campaign["id"], f"Ando pela cidade, parte {n}.")

    fake.queue("A porta se abre.")
    play(services, campaign["id"], "Uso a chave de bronze na porta da torre.")
    system_prompt = fake.calls[-1].messages[0].content
    assert "Resumo do que aconteceu antes:" in system_prompt
    assert "Lembranças de acontecimentos antigos ligados à ação atual:" in system_prompt
    assert "(turno 1)" in system_prompt and "bronze" in system_prompt


def test_search_is_isolated_between_campaigns(app_every_3):
    services = app_every_3.extensions["rpg_engine"]
    services.provider.queue("O dragão dourado dorme na montanha.")
    a = services.campaigns.create(services.local_user_id, "A", None, [])
    b = services.campaigns.create(services.local_user_id, "B", None, [])
    play(services, a["id"], "Subo a montanha.")
    with services.db.transaction() as session:
        assert CampaignData(session, b["id"]).memory_search.search("dragão dourado montanha") == []
        assert len(CampaignData(session, a["id"]).memory_search.search("dragão dourado montanha")) == 1


def test_deleting_campaign_clears_its_search_index(app_every_3):
    services = app_every_3.extensions["rpg_engine"]
    services.provider.queue("Um corvo falante pousa no ombro.")
    campaign = services.campaigns.create(services.local_user_id, "Corvo", None, [])
    play(services, campaign["id"], "Olho o céu.")
    services.campaigns.delete(services.local_user_id, campaign["id"], "Corvo")
    with services.db.transaction() as session:
        assert CampaignData(session, campaign["id"]).memory_search.search("corvo falante") == []


def test_accents_do_not_matter_in_search(app_every_3):
    services = app_every_3.extensions["rpg_engine"]
    services.provider.queue("A canção da sereia ecoa no porão.")
    campaign = services.campaigns.create(services.local_user_id, "Acentos", None, [])
    play(services, campaign["id"], "Escuto.")
    with services.db.transaction() as session:
        assert len(CampaignData(session, campaign["id"]).memory_search.search("cancao porao")) == 1
