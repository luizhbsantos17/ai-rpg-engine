"""'Gerar outra versão' da narração (como nos chatbots). FakeProvider roteirizado: lógica interna, não IA real.

Regra: só o TEXTO muda. Dados rolados e operações aplicadas ficam como estavam; se a IA falhar,
a versão anterior continua valendo.
"""

import json
import uuid

import pytest

from app import create_app
from app.ai.orchestrator.events import NarrationDelta, TurnCompleted, TurnFailed, TurnStarted
from app.persistence.models import Summary
from app.persistence.repositories import CampaignData
from app.providers import ProviderUnavailableError
from app.services.errors import ConflictError, NotFoundError

SETUP = json.dumps({
    "attributes": [{"name": "Vida", "value_type": "integer", "resource": True, "initial_value": 20}],
    "protagonist": {"name": "Kael", "description": "aprendiz de cartógrafo"},
    "starting_location": "Vila Costeira",
})
HURT = json.dumps({"intent": "lutar", "operations": [
    {"op": "attribute.modify", "entity": "player", "key": "vida", "delta": -4, "reason": "golpe"}]})


@pytest.fixture
def app(mechanics_settings):
    application = create_app(mechanics_settings)
    yield application
    application.extensions["rpg_engine"].db.dispose()


@pytest.fixture
def services(app):
    return app.extensions["rpg_engine"]


@pytest.fixture
def fake_ai(services):
    return services.provider


@pytest.fixture
def campaign(services):
    return services.campaigns.create(services.local_user_id, "Mapas Perdidos", "Os mapas sumiram.", ["mistério"])


def play(services, campaign_id, text):
    turn_id = str(uuid.uuid4())
    prepared = services.turns.prepare(services.local_user_id, campaign_id, turn_id, text)
    return turn_id, list(services.turns.run(prepared))


def regenerate(services, campaign_id, turn_id):
    prepared = services.turns.prepare_regeneration(services.local_user_id, campaign_id, turn_id)
    return list(services.turns.run(prepared))


def state(services, campaign_id):
    with services.db.transaction() as session:
        data = CampaignData(session, campaign_id)
        player = data.entities.player()
        return {
            "vida": next(a.value for a in data.attributes.for_entity(player.id) if a.definition_key == "vida"),
            "messages": [(m.role, m.content) for m in data.messages.list_ordered()],
            "dice_rolls": data.dice_rolls.count(),
            "turns": [(t.number, t.status) for t in data.turns.list_ordered()],
            "events": [e.type for e in data.events.list_ordered()],
            "found": [hit.snippet for hit in data.memory_search.search("versão")],
        }


def test_new_version_replaces_text_but_keeps_mechanics(services, fake_ai, campaign):
    fake_ai.queue(SETUP, HURT, "Primeira versão: o golpe acerta seu ombro.")
    turn_id, _ = play(services, campaign["id"], "Luto com o guarda.")
    before = state(services, campaign["id"])
    calls_before = len(fake_ai.calls)

    fake_ai.queue("Segunda versão: a lâmina raspa suas costelas.")
    events = regenerate(services, campaign["id"], turn_id)

    assert isinstance(events[0], TurnStarted) and events[0].regenerating is True
    assert "".join(e.text for e in events if isinstance(e, NarrationDelta)).startswith("Segunda versão")
    assert isinstance(events[-1], TurnCompleted) and events[-1].turn["status"] == "completed"
    assert len(fake_ai.calls) == calls_before + 1  # só o narrador: intérprete e motor não rodam de novo

    after = state(services, campaign["id"])
    assert after["vida"] == before["vida"] == "16"  # dano aplicado UMA vez
    assert after["dice_rolls"] == before["dice_rolls"]
    narrations = [text for role, text in after["messages"] if role == "narration"]
    assert narrations == ["Segunda versão: a lâmina raspa suas costelas."]
    assert [r for r, _ in after["messages"]] == [r for r, _ in before["messages"]]  # avisos [SISTEMA] continuam
    assert after["turns"] == [(1, "completed")]
    assert after["events"][-2:] == ["turn.regeneration_started", "turn.narration_regenerated"]
    assert all("Primeira" not in snippet for snippet in after["found"])  # busca da memória só tem a versão nova

    sent = fake_ai.calls[-1].messages
    assert "OUTRA VERSÃO" in sent[-1].content and "Primeira versão" in sent[-1].content  # pede algo diferente
    assert "Vida de Kael: 20 → 16" in sent[-1].content  # mesmos fatos do motor
    assert all("Primeira versão" not in m.content for m in sent[:-1])  # a versão recusada não vira histórico


def test_previous_text_is_kept_in_the_event_log(services, fake_ai, campaign):
    fake_ai.queue(SETUP, HURT, "Versão A.")
    turn_id, _ = play(services, campaign["id"], "Luto.")
    fake_ai.queue("Versão B.")
    regenerate(services, campaign["id"], turn_id)
    with services.db.transaction() as session:
        last = CampaignData(session, campaign["id"]).events.list_ordered(last=1)[0]
        assert last.type == "turn.narration_regenerated" and last.payload["previous_text"] == "Versão A."


def test_failure_keeps_the_previous_version(services, fake_ai, campaign):
    fake_ai.queue(SETUP, HURT, "Versão que fica.")
    turn_id, _ = play(services, campaign["id"], "Luto.")
    fake_ai.queue(ProviderUnavailableError("IA desligada."))
    events = regenerate(services, campaign["id"], turn_id)

    assert isinstance(events[-1], TurnFailed) and "IA desligada" in events[-1].message
    assert events[-1].turn["status"] == "completed"
    s = state(services, campaign["id"])
    assert [text for role, text in s["messages"] if role == "narration"] == ["Versão que fica."]
    assert s["turns"] == [(1, "completed")] and s["events"][-1] == "turn.regeneration_failed"


def test_client_disconnect_keeps_the_previous_version(services, fake_ai, campaign):
    fake_ai.queue(SETUP, HURT, "Versão que fica.")
    turn_id, _ = play(services, campaign["id"], "Luto.")
    fake_ai.queue("Uma versão nova bem longa que o navegador não vai ler até o fim.")
    stream = services.turns.run(services.turns.prepare_regeneration(services.local_user_id, campaign["id"], turn_id))
    next(stream)
    next(stream)
    stream.close()
    s = state(services, campaign["id"])
    assert s["turns"] == [(1, "completed")]
    assert [text for role, text in s["messages"] if role == "narration"] == ["Versão que fica."]


def test_only_the_latest_completed_turn(services, fake_ai, campaign):
    fake_ai.queue(SETUP, HURT, "Um.", json.dumps({"intent": "olhar", "operations": []}), "Dois.")
    first, _ = play(services, campaign["id"], "Luto.")
    play(services, campaign["id"], "Olho.")
    with pytest.raises(ConflictError, match="última jogada"):
        services.turns.prepare_regeneration(services.local_user_id, campaign["id"], first)
    with pytest.raises(NotFoundError):
        services.turns.prepare_regeneration(services.local_user_id, campaign["id"], str(uuid.uuid4()))

    fake_ai.queue(json.dumps({"intent": "x", "operations": []}), ProviderUnavailableError("caiu"))
    failed, _ = play(services, campaign["id"], "Corro.")
    with pytest.raises(ConflictError, match="última jogada concluída"):
        services.turns.prepare_regeneration(services.local_user_id, campaign["id"], failed)


def test_summary_that_used_the_old_text_is_redone(services, fake_ai, campaign):
    fake_ai.queue(SETUP, HURT, "Versão antiga.")
    turn_id, _ = play(services, campaign["id"], "Luto.")
    with services.db.transaction() as session:
        data = CampaignData(session, campaign["id"])
        summary = data.summaries.add(Summary(scope="scene", from_turn=1, to_turn=1, content="Resumo da versão antiga."))
        data.memory_search.index("summary", summary.id, 1, summary.content)

    fake_ai.queue("Versão nova.")
    regenerate(services, campaign["id"], turn_id)
    with services.db.transaction() as session:
        data = CampaignData(session, campaign["id"])
        assert data.summaries.last_covered_turn() == 0
        assert data.memory_search.search("antiga") == []


def test_sse_endpoint(app, services, fake_ai, campaign):
    fake_ai.queue(SETUP, HURT, "Versão A.")
    turn_id, _ = play(services, campaign["id"], "Luto.")
    fake_ai.queue("Versão B.")
    client = app.test_client()
    response = client.post(f"/api/campaigns/{campaign['id']}/turns/{turn_id}/regenerate")
    body = response.get_data(as_text=True)
    assert response.status_code == 200 and '"regenerating": true' in body and "event: done" in body
    assert client.post(f"/api/campaigns/{campaign['id']}/turns/{uuid.uuid4()}/regenerate").status_code == 404
