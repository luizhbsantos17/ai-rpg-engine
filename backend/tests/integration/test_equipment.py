"""Equipamentos (SPEC 4 e interface item 9): espaços, troca, bônus que valem nos testes do motor."""

import pytest

from app.ai.context.game_state import build_game_state
from app.ai.schemas.setup import CampaignSetup
from app.auth.local_user import ensure_local_user
from app.engine.notifications import player_notices
from app.engine.operations import OperationContext, apply_operations
from app.persistence.repositories import CampaignData, CampaignRepository
from app.services.sheet import CharacterSheetService


@pytest.fixture
def world(db):
    with db.transaction() as session:
        owner_id = ensure_local_user(session).id
        campaign_id = CampaignRepository(session, owner_id).create("Armas", rng_seed=9).id

    def run(operations):
        with db.transaction() as session:
            return apply_operations(OperationContext(CampaignData(session, campaign_id), "ai", 9), operations)

    outcomes = run([
        {"op": "definition.create", "kind": "attribute", "key": "forca", "data": {"name": "Força"}},
        {"op": "definition.create", "kind": "attribute", "key": "defesa", "data": {"name": "Defesa"}},
        {"op": "definition.create", "kind": "item", "key": "espada",
         "data": {"name": "Espada", "slot": "mao", "bonus": {"forca": 2}, "stackable": False}},
        {"op": "definition.create", "kind": "item", "key": "escudo",
         "data": {"name": "Escudo", "slot": "mao", "bonus": {"defesa": 3}}},
        {"op": "definition.create", "kind": "item", "key": "cota",
         "data": {"name": "Cota de malha", "slot": "corpo", "bonus": {"defesa": 2, "estilo": "pesado"}}},
        {"op": "definition.create", "kind": "item", "key": "anel", "data": {"name": "Anel"}},
        {"op": "entity.create", "ref": "praca", "kind": "location", "name": "Praça"},
        {"op": "entity.create", "kind": "character", "name": "Kael", "is_player": True, "location": "praca",
         "data": {"class": "guerreiro", "race": "anão"}, "attributes": {"forca": 5, "defesa": 1}},
        {"op": "entity.create", "ref": "goblin", "kind": "creature", "name": "Goblin", "location": "praca",
         "attributes": {"forca": 3}},
        {"op": "item.create", "ref": "espada", "key": "espada", "owner": "player"},
        {"op": "item.create", "ref": "escudo", "key": "escudo", "owner": "player"},
        {"op": "item.create", "ref": "cota", "key": "cota", "owner": "player"},
        {"op": "item.create", "ref": "anel", "key": "anel", "owner": "player"},
        {"op": "item.create", "ref": "chao", "key": "anel", "location": "praca", "data": {"gravado": "R"}},
    ])
    assert all(o.status == "applied" for o in outcomes), [o.reason for o in outcomes if o.status != "applied"]
    items = {ref: o.result["item_id"] for ref, o in zip(("espada", "escudo", "cota", "anel", "chao"), outcomes[-5:])}
    player_id = outcomes[7].result["entity_id"]
    goblin_id = outcomes[8].result["entity_id"]
    return run, items, player_id, goblin_id, owner_id, campaign_id


def check(run, **fields):
    outcome = run([{"op": "check.request", "actor": "player", "label": "teste", "dice": "1d20", "difficulty": 10,
                    **fields}])[0]
    assert outcome.status == "applied", outcome.reason
    return outcome.result


def test_bonus_counts_in_checks_only_while_equipped(world):
    run, items, *_ = world
    assert str(check(run, modifier="forca")["modifier"]) == "5"
    assert run([{"op": "item.equip", "item": items["espada"]}])[0].status == "applied"
    assert str(check(run, modifier="forca")["modifier"]) == "7"
    assert str(check(run, modifier="forca_base")["modifier"]) == "5"
    assert run([{"op": "item.unequip", "item": items["espada"]}])[0].status == "applied"
    assert str(check(run, modifier="forca")["modifier"]) == "5"


def test_one_item_per_slot_and_target_bonus(world):
    run, items, player_id, goblin_id, *_ = world
    outcomes = run([
        {"op": "item.equip", "item": items["espada"]},
        {"op": "item.equip", "item": items["escudo"]},  # mesma mão: troca a espada
        {"op": "item.equip", "item": items["cota"]},
    ])
    assert [o.status for o in outcomes] == ["applied"] * 3
    assert outcomes[1].result["replaced"] == "Espada"
    # defesa 1 + escudo 3 + cota 2; "estilo": "pesado" não é número e é ignorado
    result = run([{"op": "check.request", "actor": goblin_id, "target": "player", "label": "ataque",
                   "dice": "1d20", "difficulty": "target.defesa"}])[0].result
    assert str(result["difficulty"]) == "6"
    assert str(check(run, modifier="forca")["modifier"]) == "5"  # a espada saiu da mão


def test_invalid_equipping_is_refused(world):
    run, items, player_id, goblin_id, *_ = world
    outcomes = run([
        {"op": "item.equip", "item": items["anel"]},                    # sem espaço definido
        {"op": "item.equip", "item": items["espada"], "slot": "corpo"},  # espada é de mão
        {"op": "item.unequip", "item": items["cota"]},                  # não está equipada
        {"op": "item.equip", "item": items["chao"], "slot": "dedo"},     # está no chão
        {"op": "item.equip", "item": items["anel"], "slot": "dedo"},     # sem espaço fixo: vale o informado
        {"op": "item.equip", "item": items["anel"], "slot": "dedo"},     # já equipado
    ])
    assert [o.status for o in outcomes] == ["rejected", "rejected", "rejected", "rejected", "applied", "rejected"]
    assert "slot" in outcomes[0].reason and "'mao'" in outcomes[1].reason and "chão" in outcomes[3].reason


def test_giving_away_unequips(world):
    run, items, player_id, goblin_id, *_ = world
    run([{"op": "item.equip", "item": items["escudo"]}])
    transfer = run([{"op": "item.transfer", "item": items["escudo"], "to_owner": goblin_id}])[0]
    assert transfer.status == "applied" and transfer.result["unequipped_slot"] == "mao"
    result = run([{"op": "check.request", "actor": goblin_id, "label": "x", "dice": "1d20", "difficulty": 10,
                   "modifier": "defesa"}])[0]
    assert result.status == "rejected" and "defesa" in result.reason  # escudo só carregado não dá bônus


def test_player_sees_equipment_in_notices_sheet_and_ai_context(world, db):
    run, items, player_id, goblin_id, owner_id, campaign_id = world
    outcomes = run([{"op": "item.equip", "item": items["cota"]}])
    assert [n.as_message() for n in player_notices(outcomes, player_id)] == [
        "[SISTEMA] Equipado: Cota de malha (corpo) · +2 defesa, estilo pesado."]
    sheet = CharacterSheetService(db).sheet(owner_id, campaign_id)["character"]
    assert (sheet["class"], sheet["race"]) == ("guerreiro", "anão")
    equipped = {i["name"]: i["equipped_slot"] for i in sheet["items"]}
    assert equipped == {"Espada": None, "Escudo": None, "Cota de malha": "corpo", "Anel": None}
    with db.transaction() as session:
        text = build_game_state(CampaignData(session, campaign_id)).text
    assert "[equipado: corpo]" in text and "equipa em mao" in text and "bônus defesa 3" in text
    assert "classe: guerreiro; raça/espécie: anão" in text


def test_setup_keeps_class_and_race():
    setup = CampaignSetup.model_validate({
        "attributes": [{"name": "Vida", "resource": True, "initial_value": 10}],
        "protagonist": {"name": "Lyn", "character_class": "ladina", "race": " elfa "},
        "starting_location": "Torre",
    })
    player = next(op for op in setup.to_operations() if op.get("is_player"))
    assert player["data"]["class"] == "ladina" and player["data"]["race"] == "elfa"
    plain = CampaignSetup.model_validate({"attributes": [{"name": "Vida", "initial_value": 1}],
                                          "protagonist": {"name": "Sem"}, "starting_location": "X"})
    assert "class" not in next(op for op in plain.to_operations() if op.get("is_player"))["data"]
