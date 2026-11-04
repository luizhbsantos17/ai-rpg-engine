"""Regras de morte por universo (SPEC 7.4; Parte 22 caso 23)."""

import pytest

from app.ai.schemas.setup import CampaignSetup
from app.auth.local_user import ensure_local_user
from app.engine.notifications import describe_for_narrator, player_notices
from app.engine.operations import OperationContext, apply_operations
from app.persistence.repositories import CampaignData, CampaignRepository


def world_with_rule(db, rule):
    with db.transaction() as session:
        campaign_id = CampaignRepository(session, ensure_local_user(session).id).create("Morte", rng_seed=1).id

    def run(operations):
        with db.transaction() as session:
            return apply_operations(OperationContext(CampaignData(session, campaign_id), "ai", 1), operations)

    def read(fn):
        with db.transaction() as session:
            return fn(CampaignData(session, campaign_id))

    ops = [
        {"op": "definition.create", "kind": "attribute", "key": "vida",
         "data": {"name": "Vida", "value_type": "integer", "resource": True}},
        {"op": "entity.create", "kind": "character", "name": "Kael", "is_player": True, "attributes": {"vida": 10}},
        {"op": "entity.create", "ref": "lobo", "kind": "creature", "name": "Lobo", "attributes": {"vida": 5}},
    ]
    if rule is not None:
        ops.insert(1, {"op": "definition.create", "kind": "death_rule", "key": "regra",
                       "data": {"name": "Regra", "vital_resource": "vida", **rule}})
    outcomes = run(ops)
    assert all(o.status == "applied" for o in outcomes), [o.reason for o in outcomes]
    ids = {o.result["name"]: o.result["entity_id"] for o in outcomes if o.op == "entity.create"}
    return run, read, ids


def hit(run, target, damage):
    return run([{"op": "attribute.modify", "entity": target, "key": "vida", "delta": -damage}])[0]


def test_permanent_death(db):
    run, read, ids = world_with_rule(db, {"mode": "permanent", "description": "Mortos não voltam."})
    outcome = hit(run, ids["Lobo"], 9)
    assert outcome.result["death"]["mode"] == "permanent"
    assert read(lambda d: d.entities.get(ids["Lobo"]).status) == "dead"
    assert "Lobo MORREU (morte permanente neste mundo). Regra: Mortos não voltam." in describe_for_narrator([outcome])
    # Morto não age e não morre de novo.
    assert run([{"op": "check.request", "actor": ids["Lobo"], "label": "morder", "difficulty": 5}])[0].status == "rejected"
    assert "death" not in hit(run, ids["Lobo"], 1).result


def test_unconscious_then_wakes_up_when_time_passes(db):
    run, read, ids = world_with_rule(db, {"mode": "unconscious", "revive_after": "8h"})
    outcome = hit(run, "player", 15)
    assert outcome.result["death"]["returns_at"] == "dia 1, 08:00"
    assert [n.as_message() for n in player_notices([outcome], ids["Kael"])][-1] == \
        "[ALERTA] Você perdeu a consciência. (até dia 1, 08:00)"
    assert read(lambda d: d.entities.player().status) == "active"
    blocked = run([{"op": "check.request", "actor": "player", "label": "levantar", "difficulty": 5}])[0]
    assert blocked.status == "rejected" and "inconsciente" in blocked.reason

    run([{"op": "time.advance", "duration": "8h"}])
    assert read(lambda d: d.attributes.get_for(ids["Kael"], "vida").value) == "1"
    assert read(lambda d: d.effects.active_for(ids["Kael"])) == []
    assert run([{"op": "check.request", "actor": "player", "label": "levantar", "difficulty": 5}])[0].status == "applied"


def test_resurrection_after_time(db):
    run, read, ids = world_with_rule(db, {"mode": "resurrection", "revive_after": "3d", "revive_value": 4})
    hit(run, ids["Lobo"], 5)
    assert read(lambda d: d.entities.get(ids["Lobo"]).status) == "dead"
    run([{"op": "time.advance", "duration": "3d"}])
    assert read(lambda d: (d.entities.get(ids["Lobo"]).status, d.attributes.get_for(ids["Lobo"], "vida").value)) == \
        ("active", "4")


def test_reincarnation_marks_the_entity(db):
    run, read, ids = world_with_rule(db, {"mode": "reincarnation"})
    outcome = hit(run, "player", 10)
    assert read(lambda d: (d.entities.player().status if d.entities.player() else None))  # morto ainda é o protagonista
    assert read(lambda d: d.entities.get(ids["Kael"]).data["reincarnation_pending"]) is True
    assert player_notices([outcome], ids["Kael"])[-1].as_message() == "[ALERTA] Você morreu. Uma nova vida espera."


def test_without_death_rule_engine_does_nothing_automatic(db):
    run, read, ids = world_with_rule(db, None)
    outcome = hit(run, ids["Lobo"], 50)
    assert "death" not in outcome.result
    assert read(lambda d: d.entities.get(ids["Lobo"]).status) == "active"


def test_rule_cannot_be_changed_silently_to_save_someone(db):
    run, _, _ = world_with_rule(db, {"mode": "permanent"})
    outcome = run([{"op": "definition.amend", "kind": "death_rule", "key": "regra",
                    "data": {"name": "Regra", "mode": "resurrection", "vital_resource": "vida", "revive_after": "1h"}}])[0]
    assert outcome.status == "rejected" and "motivo" in outcome.reason


def test_invalid_death_rules_are_refused(db):
    run, _, _ = world_with_rule(db, None)
    outcome = run([{"op": "definition.create", "kind": "death_rule", "key": "x",
                    "data": {"name": "X", "mode": "unconscious", "vital_resource": "vida"}}])[0]
    assert outcome.status == "rejected" and "revive_after" in outcome.reason


@pytest.mark.parametrize("rule,expected_mode", [
    ({"mode": "permanent", "description": "fim"}, "permanent"),
    ({"mode": "unconscious"}, "narrative"),  # sem tempo de volta, o motor não inventa um
    ({"mode": "resurrection", "revive_after": "2d"}, "resurrection"),
])
def test_setup_creates_death_rule_for_the_first_resource(rule, expected_mode):
    setup = CampaignSetup.model_validate({
        "attributes": [{"name": "Força", "initial_value": 3}, {"name": "Vigor", "resource": True, "initial_value": 9}],
        "protagonist": {"name": "Ana"}, "starting_location": "Vila", "death_rule": rule,
    })
    created = [o for o in setup.to_operations() if o["op"] == "definition.create" and o["kind"] == "death_rule"]
    assert created[0]["data"]["vital_resource"] == "vigor" and created[0]["data"]["mode"] == expected_mode
