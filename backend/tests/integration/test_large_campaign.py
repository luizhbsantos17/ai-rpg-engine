"""Campanhas longas (Etapa 7.4): contas feitas pelo banco e contexto da IA com tamanho limitado."""

from app.ai.context.game_state import MAX_ACTIVE_QUESTS, build_game_state
from app.auth.local_user import ensure_local_user
from app.engine.operations import OperationContext, apply_operations
from app.persistence.models import Turn
from app.persistence.repositories import CampaignData, CampaignRepository


def make_campaign(db, title="Longa"):
    with db.transaction() as session:
        owner_id = ensure_local_user(session).id
        return CampaignRepository(session, owner_id).create(title, rng_seed=1).id


def test_turn_counts_come_from_the_database(db):
    campaign_id, other_id = make_campaign(db), make_campaign(db, "Outra")
    with db.transaction() as session:
        data = CampaignData(session, campaign_id)
        for n in range(1, 8):
            turn = data.turns.create(f"00000000-0000-0000-0000-{n:012d}", f"ação {n}")
            if n != 4:  # o 4º falhou
                data.turns.mark_completed(turn)
        CampaignData(session, other_id).turns.mark_completed(
            CampaignData(session, other_id).turns.create("00000000-0000-0000-0001-000000000000", "outra"))

    with db.transaction() as session:
        data = CampaignData(session, campaign_id)
        assert data.turns.count_completed() == 6  # a outra campanha não conta
        assert [t.number for t in data.turns.completed_after(2, 3)] == [3, 5, 6]
        assert all(t.status == Turn.STATUS_COMPLETED for t in data.turns.completed_after(0, 10))
        assert data.turns.completed_after(7, 5) == []


def test_active_quests_are_capped_in_ai_context(db):
    campaign_id = make_campaign(db)
    quests = [{"op": "quest.create", "key": f"missao_{n}", "title": f"Missão {n}"} for n in range(MAX_ACTIVE_QUESTS + 5)]
    with db.transaction() as session:
        outcomes = apply_operations(OperationContext(CampaignData(session, campaign_id), "ai", 1), quests)
        assert all(o.status == "applied" for o in outcomes)
    with db.transaction() as session:
        text = build_game_state(CampaignData(session, campaign_id)).text
    assert f"missao_{MAX_ACTIVE_QUESTS - 1}:" in text
    assert f"missao_{MAX_ACTIVE_QUESTS}:" not in text
    assert "... e mais 5 missões ativas." in text
