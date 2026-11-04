"""Missões (SPEC 10.1): objetivos, falha, ocultas reveladas depois."""

import pytest

from app.ai.context.game_state import build_game_state
from app.auth.local_user import ensure_local_user
from app.engine.notifications import player_notices
from app.engine.operations import OperationContext, apply_operations
from app.persistence.repositories import CampaignData, CampaignRepository
from app.services.sheet import CharacterSheetService


@pytest.fixture
def world(db):
    with db.transaction() as session:
        owner_id = ensure_local_user(session).id
        campaign_id = CampaignRepository(session, owner_id).create("Missões", rng_seed=4).id

    def run(operations):
        with db.transaction() as session:
            return apply_operations(OperationContext(CampaignData(session, campaign_id), "ai", 4), operations)

    outcomes = run([
        {"op": "entity.create", "kind": "character", "name": "Kael", "is_player": True},
        {"op": "entity.create", "ref": "oren", "kind": "character", "name": "Oren"},
        {"op": "quest.create", "key": "mapas", "title": "Os mapas perdidos", "kind": "main", "giver": "oren",
         "objectives": ["Falar com o pescador", "Encontrar o farol"]},
        {"op": "quest.create", "key": "traicao", "title": "A traição de Oren", "hidden": True},
    ])
    assert all(o.status == "applied" for o in outcomes)
    player_id = outcomes[0].result["entity_id"]
    return run, player_id, owner_id, campaign_id, outcomes


def test_objectives_and_completion(world):
    run, player_id, *_ = world
    outcomes = run([
        {"op": "quest.update", "key": "mapas", "complete_objectives": [1], "add_objectives": ["Subir a torre"]},
        {"op": "quest.update", "key": "mapas", "complete_objectives": [9]},
        {"op": "quest.update", "key": "mapas", "status": "completed"},
        {"op": "quest.update", "key": "mapas", "add_objectives": ["mais um"]},
        {"op": "quest.create", "key": "mapas", "title": "duplicada"},
    ])
    assert [o.status for o in outcomes] == ["applied", "rejected", "applied", "rejected", "rejected"]
    assert [n.as_message() for n in player_notices(outcomes, player_id)] == [
        "[MISSÃO] Os mapas perdidos: objetivo cumprido — Falar com o pescador; novo objetivo — Subir a torre.",
        "[MISSÃO] Missão concluída: Os mapas perdidos.",
    ]


def test_hidden_quest_is_secret_until_revealed(db, world):
    run, player_id, owner_id, campaign_id, created = world
    assert [n.as_message() for n in player_notices(created, player_id)] == [
        "[SISTEMA] Personagem criado: Kael.", "[MISSÃO] Nova missão: Os mapas perdidos.",
    ]
    sheet = CharacterSheetService(db).sheet(owner_id, campaign_id)
    assert [q["title"] for q in sheet["quests"]] == ["Os mapas perdidos"]
    with db.transaction() as session:
        state = build_game_state(CampaignData(session, campaign_id)).text
    assert "traicao: A traição de Oren (OCULTA para o jogador)" in state  # o mestre (IA) sabe

    revealed = run([{"op": "quest.update", "key": "traicao", "reveal": True, "add_objectives": ["Confrontar Oren"]}])
    assert [n.as_message() for n in player_notices(revealed, player_id)] == ["[MISSÃO] Nova missão: A traição de Oren."]
    sheet = CharacterSheetService(db).sheet(owner_id, campaign_id)
    assert [q["title"] for q in sheet["quests"]] == ["Os mapas perdidos", "A traição de Oren"]


def test_quests_can_fail(world):
    run, player_id, *_ = world
    outcome = run([{"op": "quest.update", "key": "mapas", "status": "failed", "reason": "o farol desabou"}])[0]
    assert outcome.status == "applied"
    assert player_notices([outcome], player_id)[0].as_message() == "[MISSÃO] Missão falhou: Os mapas perdidos."
