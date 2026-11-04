"""Mapa, diário e laços do ponto de vista do protagonista (SPEC 12.1)."""

from app.auth.local_user import ensure_local_user
from app.engine.operations import OperationContext, apply_operations
from app.persistence.models import Message, Summary
from app.persistence.repositories import CampaignData, CampaignRepository
from app.services.journal import JournalService


def test_journal_shows_only_what_the_player_experienced(db):
    with db.transaction() as session:
        owner_id = ensure_local_user(session).id
        campaign_id = CampaignRepository(session, owner_id).create("Diário", rng_seed=3).id
    with db.transaction() as session:
        data = CampaignData(session, campaign_id)
        outcomes = apply_operations(OperationContext(data, "ai", 3), [
            {"op": "definition.create", "kind": "item", "key": "pedra", "data": {"name": "Pedra brilhante"}},
            {"op": "entity.create", "ref": "vila", "kind": "location", "name": "Vila", "data": {"description": "Casas de pedra."}},
            {"op": "entity.create", "ref": "torre", "kind": "location", "name": "Torre"},
            {"op": "entity.create", "ref": "nunca", "kind": "location", "name": "Cidade Secreta"},
            {"op": "entity.create", "ref": "kael", "kind": "character", "name": "Kael", "is_player": True, "location": "vila"},
            {"op": "entity.create", "ref": "mira", "kind": "character", "name": "Mira", "location": "torre"},
            {"op": "entity.move", "entity": "player", "to": "torre"},
            {"op": "item.create", "key": "pedra", "location": "torre"},
            {"op": "relationship.change", "source": "player", "target": "mira", "changes": {"confianca": 10},
             "add_labels": ["aliada"], "cause": "lutaram juntas"},
            {"op": "relationship.change", "source": "mira", "target": "player", "changes": {"desprezo": 40},
             "cause": "segredo dela"},
        ])
        assert all(o.status == "applied" for o in outcomes), [o.reason for o in outcomes if o.reason]
        data.summaries.add(Summary(scope="scene", from_turn=1, to_turn=3, content="Kael subiu à torre."))
        data.messages.append(Message.ROLE_SYSTEM, "[MISSÃO] Nova missão: A torre.", None)
        data.messages.append(Message.ROLE_SYSTEM, "[SISTEMA] Vida: 10 → 9", None)  # não vai para o diário

    journal = JournalService(db).journal(owner_id, campaign_id)
    places = {p["name"]: p["current"] for p in journal["map"]["places"]}
    assert places == {"Vila": False, "Torre": True}  # Cidade Secreta nunca visitada
    here = journal["map"]["current"]
    assert here["name"] == "Torre" and [p["name"] for p in here["present"]] == ["Mira"]
    assert here["items"] == [{"key": "pedra", "name": "Pedra brilhante", "quantity": 1}]
    assert [e["text"] for e in journal["diary"]] == ["[MISSÃO] Nova missão: A torre.", "Kael subiu à torre."]
    assert journal["bonds"] == [{"name": "Mira", "labels": ["aliada"], "dimensions": {"confianca": 10}}]
    assert "desprezo" not in str(journal)  # o que Mira sente é oculto
