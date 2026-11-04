"""Simulação fora de cena e eventos mundiais (SPEC 8.1, 8.4, 10.2; Parte 22 caso 14)."""

import json
import uuid

import pytest

from app import create_app
from app.persistence.repositories import CampaignData
from tests.conftest import make_settings

SETUP = json.dumps({
    "attributes": [{"name": "Vida", "resource": True, "initial_value": 10}],
    "protagonist": {"name": "Kael"},
    "starting_location": "Vila",
    "companions": [{"name": "Hana", "personality": "ambiciosa", "goal": "virar guarda real", "bond": "amiga"}],
})


def ops(*operations):
    return json.dumps({"intent": "agir", "operations": list(operations)})


@pytest.fixture
def services(tmp_path, migrated_db_template):
    application = create_app(make_settings(tmp_path, migrated_db_template, AI_MECHANICS="true",
                                           AI_SIMULATION_MINUTES="360"))
    yield application.extensions["rpg_engine"]
    application.extensions["rpg_engine"].db.dispose()


def play(services, campaign_id, text):
    prepared = services.turns.prepare(services.local_user_id, campaign_id, str(uuid.uuid4()), text)
    return list(services.turns.run(prepared))


def setup_campaign(services):
    fake = services.provider
    campaign = services.campaigns.create(services.local_user_id, "Mundo Vivo", "Uma vila.", [])
    fake.queue(SETUP, ops(
        {"op": "entity.create", "ref": "porto", "kind": "location", "name": "Porto"},
        {"op": "entity.create", "kind": "character", "name": "Contrabandista", "location": "porto",
         "data": {"personality": "ganancioso"}},
        {"op": "entity.move", "entity": "e2", "to": "porto"},  # Hana vai para o porto (longe do protagonista)
    ), "Começo.")
    play(services, campaign["id"], "Começo.")
    return campaign, fake


def test_long_time_passage_simulates_relevant_npcs_elsewhere(services):
    campaign, fake = setup_campaign(services)
    with services.db.transaction() as session:
        data = CampaignData(session, campaign["id"])
        hana = next(e for e in data.entities.list() if e.name == "Hana")
        assert hana.sim_tier == 1 and data.entities.player().location_id != hana.location_id

    fake.queue(
        ops({"op": "time.advance", "duration": "2d", "reason": "viagem"}),
        json.dumps({"summary": "Hana treinou com a guarda; corre o boato de uma guerra no norte.",
                    "operations": [
                        {"op": "memory.record", "entity": "n1", "content": "Treinei com a guarda real.", "importance": 3},
                        {"op": "canon.assert", "key": "guerra_norte", "subject": "mundo",
                         "statement": "Há guerra no norte.", "status": "rumor"},
                        {"op": "time.advance", "duration": "1d"},  # proibido: o tempo já passou
                    ]}),
        "Dois dias de estrada.",
    )
    play(services, campaign["id"], "Viajo por dois dias até a capital.")

    simulation_prompt = fake.calls[-2].messages[1].content
    assert "Passaram-se 2d" in simulation_prompt
    assert "n1: Hana" in simulation_prompt and "ambiciosa" in simulation_prompt
    assert "Contrabandista" not in simulation_prompt  # nível 2 (distante): não é simulado pela IA

    narrator_input = fake.calls[-1].messages[-1].content
    assert "Hana treinou" not in narrator_input  # o protagonista não estava lá

    with services.db.transaction() as session:
        data = CampaignData(session, campaign["id"])
        hana = next(e for e in data.entities.list() if e.name == "Hana")
        assert "Treinei com a guarda real." in [m.content for m in data.memories.recall(hana.id, 10)]
        assert data.canon.current("guerra_norte").status == "rumor"
        events = [e for e in data.events.list_ordered() if e.type == "world.simulated"]
        assert events[0].payload["applied"] == 2 and events[0].payload["rejected"] == 1
        assert data.memory_search.search("guerra norte") != []
        turn = data.turns.list_ordered()[-1]
        assert turn.mechanics["simulation"]["summary"].startswith("Hana treinou")


def test_short_time_passage_does_not_call_simulation(services):
    campaign, fake = setup_campaign(services)
    calls = len(fake.calls)
    fake.queue(ops({"op": "time.advance", "duration": "1h"}), "Uma hora passa.")
    play(services, campaign["id"], "Espero uma hora.")
    assert len(fake.calls) == calls + 2  # intérprete + narrador, sem simulação


def test_invalid_simulation_json_does_not_break_the_turn(services):
    campaign, fake = setup_campaign(services)
    fake.queue(ops({"op": "time.advance", "duration": "1d"}), "não é json", "{}", "Um dia passa.")
    events = play(services, campaign["id"], "Durmo.")
    assert type(events[-1]).__name__ == "TurnCompleted"
