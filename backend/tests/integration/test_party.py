"""Turmas e grupos (SPEC 4.3; Parte 22 caso 22): cada integrante com identidade própria."""

from app.ai.context.game_state import build_game_state
from app.ai.schemas.setup import CampaignSetup
from app.auth.local_user import ensure_local_user
from app.engine.operations import OperationContext, apply_operations
from app.engine.witness import scene_knowledge_notes
from app.persistence.repositories import CampaignData, CampaignRepository

SETUP = {
    "attributes": [
        {"name": "Vida", "resource": True, "initial_value": 20},
        {"name": "Força", "initial_value": 5},
        {"name": "Mana", "resource": True, "initial_value": 10},
    ],
    "protagonist": {"name": "Yuki"},
    "starting_location": "Salão de Invocação",
    "companions": [
        {"name": "Takeshi", "personality": "arrogante e competitivo", "goal": "ser o herói escolhido",
         "bond": "rival", "attributes": {"Vida": 30, "Força": 12, "Carisma": 9}},
        {"name": "Hana", "personality": "tímida e observadora", "goal": "voltar para casa",
         "bond": "melhor amiga", "attributes": {"Vida": 14, "Mana": 40}},
    ],
}


def test_party_members_are_distinct_individuals(db):
    with db.transaction() as session:
        campaign_id = CampaignRepository(session, ensure_local_user(session).id).create("Turma", rng_seed=8).id
        data = CampaignData(session, campaign_id)
        ops = CampaignSetup.model_validate(SETUP).to_operations()
        outcomes = apply_operations(OperationContext(data, "ai", 8), ops)
        assert all(o.status == "applied" for o in outcomes), [o.reason for o in outcomes if o.reason]

        people = {e.name: e for e in data.entities.list(kind="character")}
        assert set(people) == {"Yuki", "Takeshi", "Hana"}

        def stats(name):
            return {a.definition_key: (a.value, a.max_value) for a in data.attributes.for_entity(people[name].id)}

        assert stats("Takeshi") == {"vida": ("30", "30"), "forca": ("12", None)}  # "Carisma" não existe: ignorado
        assert stats("Hana") == {"vida": ("14", "14"), "mana": ("40", "40")}
        assert people["Takeshi"].data["personality"] == "arrogante e competitivo"
        assert people["Hana"].data["goal"] == "voltar para casa"

        rival = data.relationships.between(people["Takeshi"].id, people["Yuki"].id)
        assert rival.labels == ["rival"]
        assert data.relationships.between(people["Hana"].id, people["Yuki"].id).labels == ["melhor amiga"]

        state = build_game_state(data).text
        assert "personalidade: arrogante e competitivo; objetivo: ser o herói escolhido" in state
        notes = scene_knowledge_notes(data, data.entities.player())
        assert any(n.startswith("Hana: personalidade: tímida e observadora; quer: voltar para casa") for n in notes)


def test_no_companions_when_premise_has_none():
    ops = CampaignSetup.model_validate({**SETUP, "companions": []}).to_operations()
    assert [o["name"] for o in ops if o["op"] == "entity.create"] == ["Salão de Invocação", "Yuki"]
