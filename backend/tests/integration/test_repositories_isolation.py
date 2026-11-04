"""Isolamento entre campanhas e entre donos (SPEC Parte 22, casos 2, 25 e 26)."""

import pytest

from app.auth.local_user import ensure_local_user
from app.persistence.models import Message, Turn
from app.persistence.repositories import (
    CampaignData,
    CampaignMismatchError,
    CampaignRepository,
    UserRepository,
)


@pytest.fixture
def two_campaigns(db):
    """Duas campanhas do mesmo dono, cada uma com 2 turnos, mensagens, eventos e chamadas à IA."""
    with db.transaction() as session:
        owner = ensure_local_user(session)
        campaigns = CampaignRepository(session, owner.id)
        a = campaigns.create("Campanha A")
        b = campaigns.create("Campanha B")
        for campaign in (a, b):
            data = CampaignData(session, campaign.id)
            for n in (1, 2):
                turn = data.turns.create(f"{campaign.title}-turno-{n}", f"ação {n}")
                data.messages.append(Message.ROLE_PLAYER, f"ação {n}", turn.id)
                data.messages.append(Message.ROLE_NARRATION, f"{campaign.title} narra {n}", turn.id)
                data.events.record("turn.completed", "system", {"n": n}, turn.id)
                data.ai_requests.record(turn_id=turn.id, role="narrator", provider="fake", model="m")
    return owner.id, a.id, b.id


def test_each_campaign_sees_only_its_own_data(db, two_campaigns):
    _, a_id, b_id = two_campaigns
    with db.transaction() as session:
        for campaign_id, title in ((a_id, "Campanha A"), (b_id, "Campanha B")):
            data = CampaignData(session, campaign_id)
            assert [t.number for t in data.turns.list_ordered()] == [1, 2]
            assert all(m.campaign_id == campaign_id for m in data.messages.list_ordered())
            assert [m.seq for m in data.messages.list_ordered()] == [1, 2, 3, 4]
            assert data.messages.list_ordered()[1].content == f"{title} narra 1"
            assert data.events.count() == 2
            assert len(data.ai_requests.latest()) == 2


def test_get_by_id_from_other_campaign_returns_nothing(db, two_campaigns):
    _, a_id, b_id = two_campaigns
    with db.transaction() as session:
        data_a = CampaignData(session, a_id)
        b_turn_id = "Campanha B-turno-1"
        assert data_a.turns.get(b_turn_id) is None
        assert CampaignData(session, b_id).turns.get(b_turn_id) is not None
        b_event = CampaignData(session, b_id).events.list_ordered()[0]
        assert data_a.events.get(b_event.id) is None


def test_writing_into_other_campaign_is_refused(db, two_campaigns):
    _, a_id, b_id = two_campaigns
    with pytest.raises(CampaignMismatchError):
        with db.transaction() as session:
            CampaignData(session, a_id).turns.add(Turn(id="x", campaign_id=b_id, number=9, player_input="?"))


def test_campaign_id_is_mandatory(db):
    with db.transaction() as session:
        for empty in ("", None):
            with pytest.raises(ValueError):
                CampaignData(session, empty)


def test_numbering_is_independent_per_campaign(db, two_campaigns):
    _, a_id, b_id = two_campaigns
    with db.transaction() as session:
        assert CampaignData(session, a_id).turns.create("a-3", "x").number == 3
        assert CampaignData(session, b_id).messages.append("player", "y").seq == 5


def test_recent_messages_are_in_chronological_order(db, two_campaigns):
    _, a_id, _ = two_campaigns
    with db.transaction() as session:
        assert [m.seq for m in CampaignData(session, a_id).messages.recent(3)] == [2, 3, 4]


def test_owner_cannot_see_other_owners_campaigns(db, two_campaigns):
    owner_id, a_id, _ = two_campaigns
    with db.transaction() as session:
        intruder = UserRepository(session).create("Outro jogador")
        intruder_campaigns = CampaignRepository(session, intruder.id)
        assert intruder_campaigns.get(a_id) is None
        assert intruder_campaigns.list_recent() == []
        assert len(CampaignRepository(session, owner_id).list_recent()) == 2


def test_campaign_creation_stores_intro_and_seed(db):
    with db.transaction() as session:
        owner = ensure_local_user(session)
        campaign = CampaignRepository(session, owner.id).create(
            "Com intro", ["fantasia"], {"premise": "visível"}, {"twist": "segredo"}
        )
        campaign_id = campaign.id
    with db.transaction() as session:
        stored = CampaignRepository(session, owner.id).get(campaign_id)
        assert stored.genre_tags == ["fantasia"]
        assert stored.intro.player_visible == {"premise": "visível"}
        assert stored.intro.gm_secret == {"twist": "segredo"}
        assert 0 <= stored.rng_seed < 2**63
