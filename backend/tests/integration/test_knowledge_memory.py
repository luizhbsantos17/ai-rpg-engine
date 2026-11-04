"""Conhecimento por observador e memória individual (SPEC 6.5, 8.2; Parte 22 caso 13)."""

import json
import uuid

import pytest

from app import create_app
from app.auth.local_user import ensure_local_user
from app.engine.operations import OperationContext, apply_operations
from app.engine.witness import scene_knowledge_notes
from app.persistence.repositories import CampaignData, CampaignRepository

SETUP = json.dumps({
    "attributes": [{"name": "Vida", "resource": True, "initial_value": 10}],
    "protagonist": {"name": "Kael"},
    "starting_location": "Taverna",
})


@pytest.fixture
def world(db):
    with db.transaction() as session:
        campaign_id = CampaignRepository(session, ensure_local_user(session).id).create("Saber", rng_seed=2).id

    def run(operations):
        with db.transaction() as session:
            return apply_operations(OperationContext(CampaignData(session, campaign_id), "ai", 2), operations)

    def read(fn):
        with db.transaction() as session:
            return fn(CampaignData(session, campaign_id))

    outcomes = run([
        {"op": "entity.create", "ref": "taverna", "kind": "location", "name": "Taverna"},
        {"op": "entity.create", "ref": "floresta", "kind": "location", "name": "Floresta"},
        {"op": "entity.create", "kind": "character", "name": "Kael", "is_player": True, "location": "taverna"},
        {"op": "entity.create", "kind": "character", "name": "Bram", "location": "taverna"},
        {"op": "entity.create", "kind": "character", "name": "Lia", "location": "floresta"},
    ])
    return run, read, {o.result["name"]: o.result["entity_id"] for o in outcomes}


def test_knowledge_is_per_observer(world):
    run, read, ids = world
    outcomes = run([
        {"op": "knowledge.record", "observer": ids["Bram"], "subject": "player", "field": "identidade",
         "value": "filho do rei", "level": "confirmed", "source": "ouviu"},
        {"op": "knowledge.record", "observer": ids["Lia"], "subject": "player", "field": "identidade",
         "value": "um mendigo", "level": "false", "source": "contaram"},
        {"op": "knowledge.record", "observer": ids["Bram"], "subject": "mapa_perdido", "field": "paradeiro",
         "value": "no farol", "level": "partial", "source": "deduziu"},
    ])
    assert [o.status for o in outcomes] == ["applied"] * 3

    def check(d):
        return ({k.field: (k.known_value, k.level) for k in d.knowledge.known_by(ids["Bram"], ids["Kael"])},
                {k.field: (k.known_value, k.level) for k in d.knowledge.known_by(ids["Lia"], ids["Kael"])},
                [k.subject for k in d.knowledge.known_by(ids["Kael"])])

    bram, lia, kael_knows = read(check)
    assert bram == {"identidade": ("filho do rei", "confirmed")}
    assert lia == {"identidade": ("um mendigo", "false")}
    assert kael_knows == []  # o protagonista não sabe nada disso automaticamente


def test_knowledge_update_replaces_the_observer_version(world):
    run, read, ids = world
    run([{"op": "knowledge.record", "observer": ids["Bram"], "subject": "player", "field": "forca",
          "value": "fraco", "level": "estimated", "source": "presenciou"}])
    run([{"op": "knowledge.record", "observer": ids["Bram"], "subject": "player", "field": "forca",
          "value": "forte", "level": "confirmed", "source": "avaliou"}])
    records = read(lambda d: [(k.known_value, k.level) for k in d.knowledge.known_by(ids["Bram"], ids["Kael"])])
    assert records == [("forte", "confirmed")]


def test_memories_are_individual(world):
    run, read, ids = world
    run([{"op": "memory.record", "entity": ids["Bram"], "content": "Kael me contou um segredo.", "importance": 4}])
    assert read(lambda d: [m.content for m in d.memories.recall(ids["Bram"])]) == ["Kael me contou um segredo."]
    assert read(lambda d: d.memories.recall(ids["Lia"])) == []


def test_scene_notes_only_cover_npcs_present(world):
    run, read, ids = world
    run([{"op": "memory.record", "entity": ids["Bram"], "content": "Kael pagou a bebida.", "importance": 2}])
    notes = read(lambda d: scene_knowledge_notes(d, d.entities.player()))
    assert len(notes) == 1 and notes[0].startswith("Bram: lembra: Kael pagou a bebida.")
    assert not any("Lia" in n for n in notes)


def test_witnesses_remember_the_turn_and_narrator_gets_their_knowledge(mechanics_settings):
    application = create_app(mechanics_settings)
    services = application.extensions["rpg_engine"]
    fake = services.provider
    campaign = services.campaigns.create(services.local_user_id, "Testemunhas", "Uma taverna.", [])
    first = json.dumps({"intent": "olhar", "operations": [
        {"op": "entity.create", "kind": "character", "name": "Bram", "location": "e1"},
        {"op": "entity.create", "kind": "character", "name": "Lia"},  # em lugar nenhum: não testemunha
    ]})
    fake.queue(SETUP, first, "Começo.")
    for text in ("Olho a taverna.",):
        prepared = services.turns.prepare(services.local_user_id, campaign["id"], str(uuid.uuid4()), text)
        list(services.turns.run(prepared))
    fake.queue(json.dumps({"intent": "roubar", "operations": []}), "Você pega a bolsa.")
    prepared = services.turns.prepare(services.local_user_id, campaign["id"], str(uuid.uuid4()), "Roubo a bolsa do balcão.")
    list(services.turns.run(prepared))

    with services.db.transaction() as session:
        data = CampaignData(session, campaign["id"])
        names = {e.name: e.id for e in data.entities.list()}
        bram_memories = [m.content for m in data.memories.recall(names["Bram"], 10)]
        lia_memories = data.memories.recall(names["Lia"], 10)
    assert any("Roubo a bolsa do balcão" in m for m in bram_memories)
    assert lia_memories == []
    narrator_input = fake.calls[-1].messages[-1].content
    assert "O QUE CADA PERSONAGEM PRESENTE SABE" in narrator_input and "Bram: lembra:" in narrator_input
    assert "Lia" not in narrator_input
    services.db.dispose()
