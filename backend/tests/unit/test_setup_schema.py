from app.ai.schemas.setup import CampaignSetup, slugify


def setup(**overrides):
    data = {
        "attributes": [
            {"name": "Vida", "value_type": "integer", "resource": True, "initial_value": 20},
            {"name": "Força", "value_type": "integer", "initial_value": 5},
            {"name": "Rank do Herói", "value_type": "nominal", "initial_value": "C"},
        ],
        "protagonist": {"name": "Kael", "description": "aprendiz"},
        "starting_location": "Vila Costeira",
    }
    data.update(overrides)
    return CampaignSetup.model_validate(data)


def test_slugify_removes_accents_and_spaces():
    assert slugify("Força") == "forca"
    assert slugify("Rank do Herói!") == "rank_do_heroi"
    assert slugify("???") == "atributo"


def test_operations_create_rules_location_and_protagonist_in_order():
    ops = setup().to_operations()
    assert [o["op"] for o in ops] == ["definition.create"] * 3 + ["entity.create", "entity.create"]
    assert ops[3]["kind"] == "location" and ops[3]["name"] == "Vila Costeira"
    protagonist = ops[4]
    assert protagonist["is_player"] is True and protagonist["location"] == "local_inicial"
    assert protagonist["attributes"] == {"vida": 20, "forca": 5, "rank_do_heroi": "C"}
    assert ops[1]["data"]["min"] == 0 and "min" not in ops[0]["data"]  # recurso não leva min


def test_repeated_attributes_are_dropped():
    s = setup(attributes=[
        {"name": "Vida", "resource": True, "initial_value": 20},
        {"name": "Vida", "initial_value": 30},
        {"name": "vida", "initial_value": 40},
    ])
    ops = s.to_operations()
    assert [o["key"] for o in ops if o["op"] == "definition.create"] == ["vida"]
    assert ops[-1]["attributes"] == {"vida": 20}


def test_typical_resource_is_marked_when_ai_forgot():
    s = setup(attributes=[{"name": "Força", "initial_value": 5}, {"name": "Energia", "initial_value": 10}])
    data = {o["key"]: o["data"] for o in s.to_operations() if o["op"] == "definition.create"}
    assert data["energia"]["resource"] is True and data["forca"]["resource"] is False


def test_long_companion_bond_is_cut_instead_of_refusing_the_whole_setup():
    from app.ai.schemas.setup import CampaignSetup

    setup = CampaignSetup.model_validate({
        "attributes": [{"name": "Vida", "initial_value": 10}], "protagonist": {"name": "Lia"},
        "starting_location": "Torre",
        "companions": [{"name": "Bram", "bond": "irmão de criação que jurou protegê-la desde a queda da antiga torre"}],
    })
    assert len(setup.companions[0].bond) == 60
