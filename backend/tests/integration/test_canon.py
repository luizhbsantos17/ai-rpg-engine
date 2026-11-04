"""Registro canônico (SPEC 3.4): fatos com versões; mudar exige motivo; a IA vê os fatos."""

import pytest

from app.ai.context.game_state import build_game_state
from app.ai.prompts.narrator import CampaignBrief, build_narrator_system_prompt
from app.ai.schemas.setup import CampaignSetup
from app.auth.local_user import ensure_local_user
from app.engine.operations import OperationContext, apply_operations
from app.persistence.repositories import CampaignData, CampaignRepository


@pytest.fixture
def run(db):
    with db.transaction() as session:
        campaign_id = CampaignRepository(session, ensure_local_user(session).id).create("Cânone", rng_seed=3).id

    def _run(operations):
        with db.transaction() as session:
            ctx = OperationContext(CampaignData(session, campaign_id), source="ai", campaign_seed=3)
            return [o.to_dict() for o in apply_operations(ctx, operations)]

    _run.campaign_id = campaign_id
    return _run


def test_facts_are_versioned_and_never_overwritten(db, run):
    outcomes = run([
        {"op": "canon.assert", "key": "rei", "subject": "reino", "statement": "O rei Aldric governa Valdor."},
        {"op": "canon.assert", "key": "rei", "subject": "reino", "statement": "A rainha Mira governa Valdor."},
        {"op": "canon.amend", "key": "rei", "statement": "A rainha Mira governa Valdor."},
        {"op": "canon.amend", "key": "rei", "statement": "A rainha Mira governa Valdor.", "reason": "Aldric foi deposto"},
        {"op": "canon.amend", "key": "inexistente", "statement": "x", "reason": "y"},
    ])
    assert [o["status"] for o in outcomes] == ["applied", "rejected", "rejected", "applied", "rejected"]
    assert "canon.amend" in outcomes[1]["reason"] and "motivo" in outcomes[2]["reason"]
    with db.transaction() as session:
        history = CampaignData(session, run.campaign_id).canon.history("rei")
        assert [(f.version, f.is_current, f.statement) for f in history] == [
            (1, False, "O rei Aldric governa Valdor."),
            (2, True, "A rainha Mira governa Valdor."),
        ]
        assert history[1].reason == "Aldric foi deposto"


def test_rumors_and_false_beliefs(db, run):
    run([
        {"op": "canon.assert", "key": "dragao", "subject": "lenda", "statement": "Há um dragão na montanha.", "status": "rumor"},
        {"op": "canon.assert", "key": "terra", "subject": "crença", "statement": "O mundo é plano.", "status": "false"},
    ])
    with db.transaction() as session:
        state = build_game_state(CampaignData(session, run.campaign_id)).text
    assert "[rumor] dragao: Há um dragão na montanha." in state
    assert "[crença falsa] terra: O mundo é plano." in state


def test_narrator_prompt_lists_facts_with_labels():
    prompt = build_narrator_system_prompt(CampaignBrief("T", canon=[
        ("confirmed", "A magia cobra memórias."), ("rumor", "Há um dragão."), ("false", "O mundo é plano."),
    ]))
    assert "Fatos estabelecidos do mundo" in prompt
    assert "- A magia cobra memórias." in prompt
    assert "(rumor: pode ou não ser verdade) Há um dragão." in prompt
    assert "(crença FALSA" in prompt


def test_campaign_setup_registers_world_facts_including_death_rules():
    setup = CampaignSetup.model_validate({
        "attributes": [{"name": "Vida", "resource": True, "initial_value": 10}],
        "protagonist": {"name": "Ana"},
        "starting_location": "Torre",
        "world_facts": ["A magia cobra memórias.", "  ", "Quem morre reencarna como animal."],
    })
    facts = [o for o in setup.to_operations() if o["op"] == "canon.assert"]
    assert [(f["key"], f["statement"]) for f in facts] == [
        ("mundo_1", "A magia cobra memórias."), ("mundo_2", "Quem morre reencarna como animal."),
    ]
