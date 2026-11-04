"""Relacionamentos (SPEC 9; Parte 22 caso 15): direcionais, multidimensionais, com causa registrada."""

import pytest

from app.ai.context.game_state import build_game_state
from app.auth.local_user import ensure_local_user
from app.engine.notifications import describe_for_narrator, player_notices
from app.engine.operations import OperationContext, apply_operations
from app.persistence.repositories import CampaignData, CampaignRepository

WORLD = [
    {"op": "entity.create", "ref": "praca", "kind": "location", "name": "Praça"},
    {"op": "entity.create", "ref": "kael", "kind": "character", "name": "Kael", "is_player": True, "location": "praca"},
    {"op": "entity.create", "ref": "mira", "kind": "character", "name": "Mira", "location": "praca"},
]


@pytest.fixture
def world(db):
    with db.transaction() as session:
        campaign_id = CampaignRepository(session, ensure_local_user(session).id).create("Social", rng_seed=5).id

    def run(operations):
        with db.transaction() as session:
            ctx = OperationContext(CampaignData(session, campaign_id), source="ai", campaign_seed=5)
            return apply_operations(ctx, operations)

    def read(fn):
        with db.transaction() as session:
            return fn(CampaignData(session, campaign_id))

    outcomes = run(WORLD)
    ids = {o.result["name"]: o.result["entity_id"] for o in outcomes}
    return run, read, ids


def test_relationship_is_directional_and_keeps_causes(world):
    run, read, ids = world
    outcomes = run([
        {"op": "relationship.change", "source": ids["Mira"], "target": "player",
         "changes": {"confianca": 15, "medo": -5}, "add_labels": ["salva por Kael"],
         "cause": "Kael a salvou do incêndio"},
        {"op": "relationship.change", "source": ids["Mira"], "target": "player",
         "changes": {"confianca": -40}, "cause": "Kael mentiu sobre o mapa"},
    ])
    assert [o.status for o in outcomes] == ["applied", "applied"]

    def check(d):
        mira_to_kael = d.relationships.between(ids["Mira"], ids["Kael"])
        kael_to_mira = d.relationships.between(ids["Kael"], ids["Mira"])
        history = d.relationships.history(mira_to_kael.id)
        return mira_to_kael.dimensions, mira_to_kael.labels, kael_to_mira, [h.cause for h in history]

    dimensions, labels, reverse, causes = read(check)
    assert dimensions == {"confianca": -25, "medo": -5}
    assert labels == ["salva por Kael"]
    assert reverse is None  # o que Kael sente por Mira não mudou
    assert causes == ["Kael a salvou do incêndio", "Kael mentiu sobre o mapa"]


def test_limits_and_required_cause(world):
    run, _, ids = world
    outcomes = run([
        {"op": "relationship.change", "source": ids["Mira"], "target": "player", "changes": {"afeto": 90}, "cause": "x"},
        {"op": "relationship.change", "source": ids["Mira"], "target": "player", "changes": {"afeto": 10}},
        {"op": "relationship.change", "source": ids["Mira"], "target": ids["Mira"], "changes": {"afeto": 1}, "cause": "x"},
        {"op": "relationship.change", "source": ids["Mira"], "target": "player", "cause": "nada mudou"},
    ])
    assert [o.status for o in outcomes] == ["rejected"] * 4
    assert "±50" in outcomes[0].reason


def test_values_stay_in_the_common_range(world):
    run, read, ids = world
    for _ in range(4):
        run([{"op": "relationship.change", "source": ids["Mira"], "target": "player",
              "changes": {"respeito": 40}, "cause": "outro feito heroico"}])
    assert read(lambda d: d.relationships.between(ids["Mira"], ids["Kael"]).dimensions["respeito"]) == 100


def test_relationship_reaches_interpreter_and_narrator_but_not_player_notices(world):
    run, read, ids = world
    outcome = run([{"op": "relationship.change", "source": ids["Mira"], "target": "player",
                    "changes": {"ciume": 20}, "add_labels": ["rival amorosa"], "cause": "viu Kael com outra"}])[0]
    state = read(lambda d: build_game_state(d).text)
    assert "sente pelo protagonista: ciume=20; rótulos: rival amorosa" in state
    line = describe_for_narrator([outcome])[0]
    assert "O que Mira sente por Kael mudou: ciume +20 (agora 20)" in line and "viu Kael com outra" in line
    assert player_notices([outcome], ids["Kael"]) == []  # sentimentos de NPC são ocultos
