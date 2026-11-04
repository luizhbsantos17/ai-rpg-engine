"""Avaliação, ocultação e falsificação (SPEC Parte 6; Parte 22 casos 10, 11 e 12).

Dado "1d1" (sempre 1) deixa o total exato: total = 1 + poder. Dificuldade = 10 + força da ocultação.
"""

import pytest

from app.auth.local_user import ensure_local_user
from app.engine.notifications import describe_for_narrator, player_notices
from app.engine.operations import OperationContext, apply_operations
from app.persistence.repositories import CampaignData, CampaignRepository
from app.services.known import KnownCharactersService

WORLD = [
    {"op": "definition.create", "kind": "attribute", "key": "forca", "data": {"name": "Força", "value_type": "integer"}},
    {"op": "definition.create", "kind": "attribute", "key": "vida", "data": {"name": "Vida", "value_type": "integer", "resource": True}},
    {"op": "definition.create", "kind": "attribute", "key": "ouro", "data": {"name": "Ouro", "value_type": "integer"}},
    {"op": "entity.create", "ref": "rua", "kind": "location", "name": "Rua"},
    {"op": "entity.create", "kind": "character", "name": "Kael", "is_player": True, "location": "rua",
     "attributes": {"forca": 5, "vida": 20}},
    {"op": "entity.create", "kind": "character", "name": "Viajante", "location": "rua",
     "data": {"true_identity": "Príncipe Aurel, herdeiro exilado"},
     "attributes": {"forca": 14, "vida": {"value": 37, "max": 40}, "ouro": 1234}},
]


@pytest.fixture
def world(db):
    with db.transaction() as session:
        owner_id = ensure_local_user(session).id
        campaign_id = CampaignRepository(session, owner_id).create("Olhos", rng_seed=6).id

    def run(operations):
        with db.transaction() as session:
            return apply_operations(OperationContext(CampaignData(session, campaign_id), "ai", 6), operations)

    outcomes = run(WORLD)
    assert all(o.status == "applied" for o in outcomes)
    ids = {o.result["name"]: o.result.get("entity_id") for o in outcomes if o.op == "entity.create"}
    return run, ids, owner_id, campaign_id


def assess(run, ids, fields, power, **extra):
    outcome = run([{"op": "knowledge.assess", "observer": "player", "target": ids["Viajante"], "label": "Olhar Analítico",
                    "fields": fields, "power": power, "dice": "1d1", **extra}])[0]
    assert outcome.status == "applied", outcome.reason
    return outcome, {f["field"]: (f["level"], f["value"]) for f in outcome.result["findings"]}


def test_no_concealment_success_reveals_truth(world):
    run, ids, *_ = world
    _, findings = assess(run, ids, ["forca", "vida"], power=9)  # total 10 vs 10
    assert findings == {"forca": ("confirmed", "14"), "vida": ("confirmed", "37/40")}


def test_near_miss_gives_only_an_estimate(world):
    run, ids, *_ = world
    _, findings = assess(run, ids, ["forca", "ouro", "vida"], power=6)  # margem -3
    assert findings == {"forca": ("estimated", "≈10"), "ouro": ("estimated", "≈1000"), "vida": ("estimated", "≈40")}


def test_concealed_status_hides_information(world):
    run, ids, *_ = world
    run([{"op": "disguise.apply", "entity": ids["Viajante"], "field": "forca", "power": 30}])
    _, findings = assess(run, ids, ["forca", "vida"], power=9)
    assert findings == {"forca": ("unknown", None), "vida": ("confirmed", "37/40")}  # só a força estava oculta


def test_partial_and_critical_against_concealment(world):
    run, ids, *_ = world
    run([{"op": "disguise.apply", "entity": ids["Viajante"], "field": "*", "power": 0}])
    _, partial = assess(run, ids, ["forca"], power=9)  # margem 0 com ocultação
    assert partial == {"forca": ("partial", "14")}
    outcome, critical = assess(run, ids, ["forca"], power=19)  # margem 10
    assert critical == {"forca": ("confirmed", "14")}
    assert outcome.result["findings"][0]["noticed_concealment"] is True


def test_falsified_identity_deceives_and_player_does_not_know(db, world):
    run, ids, owner_id, campaign_id = world
    run([{"op": "disguise.apply", "entity": ids["Viajante"], "field": "identity",
          "presented_value": "um mercador comum", "power": 30}])
    outcome, findings = assess(run, ids, ["identity"], power=0)
    assert findings == {"identity": ("false", "um mercador comum")}

    narrator = describe_for_narrator([outcome])[0]
    assert "ENGANADO" in narrator and "Príncipe Aurel" in narrator  # o mestre sabe a verdade
    notice = player_notices([outcome], ids["Kael"])[0].as_message()
    assert notice == "[ANÁLISE] Viajante: identity = um mercador comum (confirmado)."
    assert "Príncipe" not in notice

    known = KnownCharactersService(db).known(owner_id, campaign_id)["characters"]
    assert known == [{"id": ids["Viajante"], "name": "Viajante", "kind": "character",
                      "facts": [{"field": "identity", "value": "um mercador comum", "level": "confirmed"}]}]


def test_true_status_never_leaks_to_the_player_view(db, world):
    run, ids, owner_id, campaign_id = world
    assess(run, ids, ["forca"], power=9)
    known = KnownCharactersService(db).known(owner_id, campaign_id)["characters"][0]
    assert [f["field"] for f in known["facts"]] == ["forca"]  # nada de vida, ouro ou identidade


def test_target_can_notice_the_assessment(db, world):
    run, ids, _, campaign_id = world
    outcome, _ = assess(run, ids, ["forca"], power=0, detection=100)
    assert outcome.result["detected"] is True
    with db.transaction() as session:
        memories = [m.content for m in CampaignData(session, campaign_id).memories.recall(ids["Viajante"])]
    assert "Percebeu que Kael tentou avaliá-lo." in memories

    reverse = run([{"op": "knowledge.assess", "observer": ids["Viajante"], "target": "player", "fields": ["forca"],
                    "power": 0, "dice": "1d1", "detection": 100}])[0]
    assert player_notices([reverse], ids["Kael"])[0].as_message() == "[ALERTA] Você sentiu que Viajante tentou avaliá-lo."


def test_assessment_rules(world):
    run, ids, *_ = world
    outcomes = run([
        {"op": "knowledge.assess", "observer": "player", "target": "player", "fields": ["forca"]},
        {"op": "knowledge.assess", "observer": "player", "target": ids["Viajante"], "fields": ["carisma"]},
        {"op": "disguise.remove", "entity": ids["Viajante"], "field": "forca"},
    ])
    assert [o.status for o in outcomes] == ["rejected"] * 3
