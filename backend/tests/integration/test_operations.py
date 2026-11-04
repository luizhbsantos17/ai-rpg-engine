"""Pipeline de operações do motor (SPEC Parte 22: casos 5–8, 19 e 20)."""

import pytest

from app.auth.local_user import ensure_local_user
from app.engine.operations import OperationContext, apply_operations
from app.persistence.models import Entity, ItemInstance
from app.persistence.repositories import CampaignData, CampaignRepository

BASE_RULES = [
    {"op": "definition.create", "kind": "attribute", "key": "forca",
     "data": {"name": "Força", "value_type": "integer", "min": 0}},
    {"op": "definition.create", "kind": "attribute", "key": "vida",
     "data": {"name": "Vida", "value_type": "integer", "resource": True}},
    {"op": "definition.create", "kind": "attribute", "key": "mana",
     "data": {"name": "Mana", "value_type": "decimal", "resource": True}},
    {"op": "definition.create", "kind": "attribute", "key": "rank",
     "data": {"name": "Rank", "value_type": "nominal", "scale": ["F", "E", "D", "C", "B", "A", "S"]}},
    {"op": "definition.create", "kind": "skill", "key": "bola_de_fogo",
     "data": {"name": "Bola de Fogo", "costs": [{"resource": "mana", "amount": "10"}], "max_level": 10,
              "efeito_inedito": "queima memórias"}},
    {"op": "definition.create", "kind": "skill", "key": "eco_do_destino", "data": {"name": "Eco do Destino"}},
    {"op": "definition.create", "kind": "item", "key": "pocao", "data": {"name": "Poção", "stackable": True}},
    {"op": "definition.create", "kind": "item", "key": "espada", "data": {"name": "Espada", "stackable": False}},
    {"op": "entity.create", "ref": "taverna", "kind": "location", "name": "Taverna do Corvo"},
    {"op": "entity.create", "ref": "heroi", "kind": "character", "name": "Aria", "is_player": True,
     "location": "taverna",
     "attributes": {"forca": 12, "vida": {"value": 30, "max": 40}, "mana": 25.5, "rank": "C"}},
    {"op": "entity.create", "ref": "goblin", "kind": "creature", "name": "Goblin", "location": "taverna",
     "attributes": {"forca": 5, "vida": 10}},
]


@pytest.fixture
def campaign_id(db):
    with db.transaction() as session:
        owner = ensure_local_user(session)
        return CampaignRepository(session, owner.id).create("Motor", rng_seed=777).id


@pytest.fixture
def run(db, campaign_id):
    """Aplica uma lista de operações numa transação e devolve os resultados."""

    def _run(operations, source="ai", turn_id=None):
        with db.transaction() as session:
            ctx = OperationContext(CampaignData(session, campaign_id), source=source, campaign_seed=777, turn_id=turn_id)
            outcomes = apply_operations(ctx, operations)
            return [o.to_dict() for o in outcomes]

    return _run


@pytest.fixture
def world(run):
    outcomes = run(BASE_RULES)
    assert [o["status"] for o in outcomes] == ["applied"] * len(BASE_RULES), outcomes
    return {o["result"]["name"]: o["result"].get("entity_id") for o in outcomes if o["op"] == "entity.create"}


def read(db, campaign_id, fn):
    with db.transaction() as session:
        return fn(CampaignData(session, campaign_id))


def attrs(data, entity_id):
    return {a.definition_key: (a.value, a.max_value) for a in data.attributes.for_entity(entity_id)}


def test_world_creation_persists_attributes_of_every_type(db, campaign_id, world):
    values = read(db, campaign_id, lambda d: attrs(d, world["Aria"]))
    assert values == {"forca": ("12", None), "vida": ("30", "40"), "mana": ("25.5", "25.5"), "rank": ("C", None)}
    player = read(db, campaign_id, lambda d: (d.entities.player().name, d.entities.player().location_id))
    assert player == ("Aria", world["Taverna do Corvo"])


def test_open_definitions_keep_free_properties(db, campaign_id, world):
    data = read(db, campaign_id, lambda d: d.definitions.current("skill", "bola_de_fogo").data)
    assert data["efeito_inedito"] == "queima memórias"


def test_attribute_changes_and_resource_limits(db, campaign_id, run, world):
    outcomes = run([
        {"op": "attribute.modify", "entity": "player", "key": "forca", "delta": 3, "reason": "treino"},
        {"op": "resource.spend", "entity": "player", "key": "mana", "amount": 10.5},
        {"op": "resource.restore", "entity": "player", "key": "vida", "amount": 100},
        {"op": "attribute.modify", "entity": "goblin_inexistente", "key": "forca", "delta": 1},
        {"op": "attribute.modify", "entity": world["Goblin"], "key": "vida", "delta": "-forca * 3"},
        {"op": "attribute.set", "entity": "player", "key": "rank", "value": "S"},
        {"op": "attribute.set", "entity": "player", "key": "rank", "value": "SSS"},
        {"op": "resource.spend", "entity": "player", "key": "mana", "amount": 1000},
    ])
    assert [o["status"] for o in outcomes] == [
        "applied", "applied", "applied", "rejected", "applied", "applied", "rejected", "rejected",
    ]
    assert outcomes[2]["result"]["to"] == "40"  # recuperação limitada ao máximo
    assert outcomes[4]["result"]["to"] == "0" and outcomes[4]["result"]["clamped"] is True  # 10 - 15, mínimo 0
    assert "escala" in outcomes[6]["reason"]
    assert "suficiente" in outcomes[7]["reason"]
    values = read(db, campaign_id, lambda d: attrs(d, world["Aria"]))
    assert values["forca"] == ("15", None) and values["mana"] == ("15", "25.5") and values["rank"] == ("S", None)


def test_no_artificial_ceiling(db, campaign_id, run, world):
    outcomes = run([{"op": "attribute.modify", "entity": "player", "key": "forca", "delta": "1e40"}])
    assert outcomes[0]["status"] == "applied"
    assert read(db, campaign_id, lambda d: attrs(d, world["Aria"])["forca"][0]) == "10000000000000000000000000000000000000012"


def test_integer_attribute_refuses_fractions_and_undefined_attributes(run, world):
    outcomes = run([
        {"op": "attribute.set", "entity": "player", "key": "forca", "value": 2.5},
        {"op": "attribute.set", "entity": "player", "key": "carisma", "value": 3},
        {"op": "attribute.set", "entity": "player", "key": "forca", "value": -1},
    ])
    assert [o["status"] for o in outcomes] == ["rejected"] * 3
    assert "inteiros" in outcomes[0]["reason"] and "definido" in outcomes[1]["reason"]


def test_skills_grant_evolve_revoke_and_limits(db, campaign_id, run, world):
    outcomes = run([
        {"op": "skill.grant", "entity": "player", "key": "bola_de_fogo"},
        {"op": "skill.grant", "entity": "player", "key": "bola_de_fogo"},
        {"op": "skill.evolve", "entity": "player", "key": "bola_de_fogo", "levels": 4},
        {"op": "skill.evolve", "entity": "player", "key": "bola_de_fogo", "levels": 20},
        {"op": "skill.grant", "entity": "player", "key": "habilidade_que_nao_existe"},
        {"op": "skill.grant", "entity": "player", "key": "eco_do_destino", "level": 999999},
        {"op": "skill.revoke", "entity": "player", "key": "eco_do_destino", "reason": "selado"},
    ])
    assert [o["status"] for o in outcomes] == ["applied", "rejected", "applied", "rejected", "rejected", "applied", "applied"]
    assert outcomes[2]["result"]["to"] == 5
    assert "máximo 10" in outcomes[3]["reason"]
    skills = read(db, campaign_id, lambda d: {s.definition_key: s.level for s in d.skills.for_entity(world["Aria"])})
    assert skills == {"bola_de_fogo": 5}


def test_inventory_without_duplication(db, campaign_id, run, world):
    created = run([
        {"op": "item.create", "ref": "p", "key": "pocao", "owner": "player", "quantity": 3},
        {"op": "item.create", "key": "pocao", "owner": "player", "quantity": 2},
        {"op": "item.create", "ref": "espada", "key": "espada", "location": world["Taverna do Corvo"]},
        {"op": "item.create", "key": "espada", "owner": "player", "quantity": 2},
        {"op": "item.create", "key": "pocao", "owner": "player", "location": world["Taverna do Corvo"]},
    ])
    assert [o["status"] for o in created] == ["applied", "applied", "applied", "rejected", "rejected"]
    assert created[1]["result"]["total_quantity"] == 5  # empilhou
    potion_id, sword_id = created[0]["result"]["item_id"], created[2]["result"]["item_id"]

    moved = run([
        {"op": "item.transfer", "item": potion_id, "to_owner": world["Goblin"], "quantity": 2},
        {"op": "item.transfer", "item": sword_id, "to_owner": "player"},
        {"op": "item.transfer", "item": sword_id, "to_owner": "player"},
        {"op": "item.transfer", "item": potion_id, "to_owner": world["Goblin"], "quantity": 99},
        {"op": "item.destroy", "item": potion_id, "quantity": 1},
    ])
    assert [o["status"] for o in moved] == ["applied", "applied", "rejected", "rejected", "applied"]

    def inventory(d):
        def held(entity_id):
            return sorted((i.definition_key, i.quantity) for i in d.items.held_by(entity_id))

        return held(world["Aria"]), held(world["Goblin"]), d.items.active_ids_conflicting()

    aria, goblin, conflicts = read(db, campaign_id, inventory)
    assert aria == [("espada", 1), ("pocao", 2)]
    assert goblin == [("pocao", 2)]
    assert conflicts == []


def test_check_is_rolled_by_engine_reproducibly_and_recorded(db, campaign_id, run, world):
    check = {"op": "check.request", "actor": "player", "target": world["Goblin"], "label": "Ataque com espada",
             "dice": "1d20", "modifier": "forca - target.forca", "difficulty": 10,
             "critical_success": 20, "critical_failure": 1}
    first = run([check], turn_id=None)[0]
    assert first["status"] == "applied"
    result = first["result"]
    assert result["modifier"] == "7"  # 12 - 5
    assert result["total"] == str(result["natural"] + 7)
    natural = result["natural"]
    expected = natural != 1 and (natural + 7 >= 10 or natural == 20)
    assert result["success"] is expected
    assert result["critical_success"] is (natural == 20) and result["critical_failure"] is (natural == 1)
    assert read(db, campaign_id, lambda d: d.dice_rolls.count()) == 1  # registrada com a semente
    # Mesmo contexto (semente da campanha + turno + contador) = mesmo resultado.
    again = run([check], turn_id=None)[0]["result"]
    assert again["dice"] == result["dice"]
    assert read(db, campaign_id, lambda d: d.dice_rolls.count()) == 2


def test_operations_conditioned_on_check_results(db, campaign_id, run, world):
    outcomes = run([
        {"op": "check.request", "ref": "ataque", "actor": "player", "target": world["Goblin"],
         "label": "Golpe", "difficulty": 11},
        {"op": "attribute.modify", "entity": world["Goblin"], "key": "vida", "delta": -4,
         "when": {"check": "ataque", "success": True}},
        {"op": "attribute.modify", "entity": "player", "key": "vida", "delta": -2,
         "when": {"check": "ataque", "success": False}},
        {"op": "attribute.modify", "entity": "player", "key": "vida", "delta": -1,
         "when": {"check": "teste_inexistente"}},
    ])
    success = outcomes[0]["result"]["success"]
    assert [o["status"] for o in outcomes[1:3]] == (["applied", "skipped"] if success else ["skipped", "applied"])
    assert outcomes[3]["status"] == "rejected"
    goblin_life = read(db, campaign_id, lambda d: attrs(d, world["Goblin"])["vida"][0])
    player_life = read(db, campaign_id, lambda d: attrs(d, world["Aria"])["vida"][0])
    assert (goblin_life, player_life) == (("6", "30") if success else ("10", "28"))


def test_check_cannot_be_decided_by_the_ai(run, world):
    outcomes = run([{"op": "check.request", "actor": "player", "label": "x", "difficulty": 10, "result": 20}])
    assert outcomes[0]["status"] == "rejected"
    assert "result" in outcomes[0]["reason"]


def test_rules_are_versioned_not_overwritten(db, campaign_id, run, world):
    outcomes = run([
        {"op": "definition.create", "kind": "attribute", "key": "forca", "data": {"name": "Força 2"}},
        {"op": "definition.amend", "kind": "attribute", "key": "forca", "data": {"name": "Força Bruta", "value_type": "integer"}},
        {"op": "definition.amend", "kind": "attribute", "key": "forca",
         "data": {"name": "Força Bruta", "value_type": "integer"}, "reason": "o deus da guerra abençoou o mundo"},
    ])
    assert [o["status"] for o in outcomes] == ["rejected", "rejected", "applied"]
    history = read(db, campaign_id, lambda d: [(x.version, x.is_current, x.data["name"]) for x in d.definitions.history("attribute", "forca")])
    assert history == [(1, False, "Força"), (2, True, "Força Bruta")]


def test_invalid_ai_output_never_corrupts_state(db, campaign_id, run, world):
    outcomes = run([
        "isto não é uma operação",
        {"op": "apagar.banco"},
        {"op": "attribute.set"},
        {"op": "entity.create", "ref": "fantasma", "kind": "character", "name": "Fantasma",
         "attributes": {"atributo_inexistente": 1}},
        {"op": "attribute.set", "entity": "fantasma", "key": "forca", "value": 1},
        {"op": "definition.create", "kind": "skill", "key": "chave invalida", "data": {"name": "x"}},
        {"op": "definition.create", "kind": "skill", "key": "golpe", "data": {"name": "Golpe", "damage": "__import__('os')"}},
        {"op": "attribute.modify", "entity": "player", "key": "forca", "delta": 1},
    ])
    assert [o["status"] for o in outcomes] == ["rejected"] * 7 + ["applied"]
    # A entidade com atributo inválido foi totalmente desfeita (nada pela metade).
    names = read(db, campaign_id, lambda d: [e.name for e in d.entities.list()])
    assert "Fantasma" not in names
    rejected = read(db, campaign_id, lambda d: [e.payload["reason"] for e in d.events.list_ordered() if e.type == "operation.rejected"])
    assert len(rejected) == 7


def test_entities_status_move_and_cycles(db, campaign_id, run, world):
    outcomes = run([
        {"op": "entity.create", "ref": "bau", "kind": "container", "name": "Baú", "location": world["Taverna do Corvo"]},
        {"op": "entity.move", "entity": world["Taverna do Corvo"], "to": "bau"},
        {"op": "entity.update", "entity": world["Goblin"], "status": "dead", "reason": "derrotado"},
        {"op": "skill.grant", "entity": world["Goblin"], "key": "eco_do_destino"},
        {"op": "entity.remove", "entity": "player"},
        {"op": "entity.remove", "entity": world["Goblin"]},
        {"op": "entity.move", "entity": world["Goblin"], "to": "bau"},
    ])
    assert [o["status"] for o in outcomes] == ["applied", "rejected", "applied", "rejected", "rejected", "applied", "rejected"]
    statuses = read(db, campaign_id, lambda d: {e.name: e.status for e in d.entities.list(include_removed=True)})
    assert statuses["Goblin"] == Entity.STATUS_REMOVED


def test_every_applied_operation_is_in_the_event_log(db, campaign_id, run, world):
    events = read(db, campaign_id, lambda d: [(e.type, e.source) for e in d.events.list_ordered()])
    assert [t for t, _ in events] == [op["op"] for op in BASE_RULES]
    assert {s for _, s in events} == {"ai"}


def test_isolation_between_campaigns(db, run, world):
    with db.transaction() as session:
        owner = ensure_local_user(session)
        other_id = CampaignRepository(session, owner.id).create("Outra", rng_seed=1).id
    with db.transaction() as session:
        ctx = OperationContext(CampaignData(session, other_id), source="ai", campaign_seed=1)
        outcomes = apply_operations(ctx, [
            {"op": "attribute.set", "entity": world["Aria"], "key": "forca", "value": 1},
            {"op": "item.create", "key": "pocao", "owner": world["Aria"]},
        ])
    assert [o.status for o in outcomes] == ["rejected", "rejected"]


def test_destroyed_items_stay_in_history(db, campaign_id, run, world):
    item_id = run([{"op": "item.create", "key": "espada", "owner": "player"}])[0]["result"]["item_id"]
    run([{"op": "item.destroy", "item": item_id}])
    status = read(db, campaign_id, lambda d: d.items.get(item_id).status)
    assert status == ItemInstance.STATUS_DESTROYED
    assert run([{"op": "item.transfer", "item": item_id, "to_owner": world["Goblin"]}])[0]["status"] == "rejected"
