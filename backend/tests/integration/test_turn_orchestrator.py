"""Pipeline do turno com FakeProvider (lógica interna; não é integração real com IA)."""

import uuid

import pytest

from app.ai.orchestrator.events import NarrationDelta, TurnCompleted, TurnFailed, TurnStarted
from app.persistence.models import Turn
from app.persistence.repositories import CampaignData
from app.providers import ProviderResponseError, ProviderUnavailableError
from app.providers.fake import FailMidStream
from app.services.errors import ConflictError, InvalidInputError, NotFoundError
from app.services.startup import initialize_services


@pytest.fixture
def campaign(services):
    return services.campaigns.create(services.local_user_id, "Reino de Teste", "Um reino em crise.", ["fantasia"])


def play(services, campaign_id, text, turn_id=None):
    turn_id = turn_id or str(uuid.uuid4())
    prepared = services.turns.prepare(services.local_user_id, campaign_id, turn_id, text)
    return turn_id, list(services.turns.run(prepared))


def stored(services, campaign_id):
    with services.db.transaction() as session:
        data = CampaignData(session, campaign_id)
        turns = [(t.number, t.status, t.error) for t in data.turns.list_ordered()]
        messages = [(m.seq, m.role, m.content) for m in data.messages.list_ordered()]
        events = [e.type for e in data.events.list_ordered()]
        requests = [(r.model, r.error, r.tokens_out) for r in reversed(data.ai_requests.latest(50))]
    return turns, messages, events, requests


def test_successful_turn_is_streamed_and_saved(services, fake_ai, campaign):
    fake_ai.queue("A porta range e revela um salão escuro.")
    _, events = play(services, campaign["id"], "Abro a porta.")

    assert isinstance(events[0], TurnStarted) and not events[0].replay
    assert "".join(e.text for e in events if isinstance(e, NarrationDelta)) == "A porta range e revela um salão escuro."
    assert isinstance(events[-1], TurnCompleted)
    assert events[-1].turn["status"] == "completed"

    turns, messages, event_types, requests = stored(services, campaign["id"])
    assert turns == [(1, "completed", None)]
    assert messages == [(1, "player", "Abro a porta."), (2, "narration", "A porta range e revela um salão escuro.")]
    assert event_types == ["campaign.created", "turn.started", "turn.completed"]
    assert requests == [("fake-model", None, 8)]


def test_context_contains_rules_campaign_history_and_current_input(services, fake_ai, campaign):
    fake_ai.queue("Primeira narração.", "Segunda narração.")
    play(services, campaign["id"], "Primeira ação.")
    play(services, campaign["id"], "Segunda ação.")

    sent = fake_ai.calls[1].messages
    assert sent[0].role == "system"
    assert "Reino de Teste" in sent[0].content and "Um reino em crise." in sent[0].content
    assert "Nunca decida pelo jogador" in sent[0].content
    assert [(m.role, m.content) for m in sent[1:]] == [
        ("user", "Primeira ação."), ("assistant", "Primeira narração."), ("user", "Segunda ação."),
    ]


def test_repeating_completed_turn_returns_saved_narration_without_calling_ai(services, fake_ai, campaign):
    fake_ai.queue("Narração única.")
    turn_id, _ = play(services, campaign["id"], "Olho em volta.")
    _, again = play(services, campaign["id"], "Olho em volta.", turn_id=turn_id)

    assert again[0].replay is True
    assert again[-1].narration_message["content"] == "Narração única."
    assert len(fake_ai.calls) == 1
    turns, messages, _, _ = stored(services, campaign["id"])
    assert len(turns) == 1 and len(messages) == 2


def test_provider_failure_marks_turn_failed_and_retry_succeeds(services, fake_ai, campaign):
    fake_ai.queue(ProviderUnavailableError("Ollama desligado."), "Agora funcionou.")
    turn_id, events = play(services, campaign["id"], "Ataco o goblin.")
    assert isinstance(events[-1], TurnFailed)
    assert events[-1].retryable is True and "Ollama desligado" in events[-1].message

    turns, messages, _, requests = stored(services, campaign["id"])
    assert turns == [(1, "failed", "Ollama desligado.")]
    assert messages == [(1, "player", "Ataco o goblin.")]
    assert requests[0][1] == "Ollama desligado."

    _, retry = play(services, campaign["id"], "Ataco o goblin.", turn_id=turn_id)
    assert isinstance(retry[-1], TurnCompleted)
    turns, messages, event_types, _ = stored(services, campaign["id"])
    assert turns == [(1, "completed", None)]
    assert messages == [(1, "player", "Ataco o goblin."), (2, "narration", "Agora funcionou.")]
    assert event_types[-3:] == ["turn.failed", "turn.retried", "turn.completed"]


def test_failure_in_the_middle_saves_no_partial_narration(services, fake_ai, campaign):
    fake_ai.queue(FailMidStream("Meio texto", ProviderResponseError("caiu")))
    _, events = play(services, campaign["id"], "Corro.")
    assert any(isinstance(e, NarrationDelta) for e in events)
    assert isinstance(events[-1], TurnFailed)
    turns, messages, _, _ = stored(services, campaign["id"])
    assert turns[0][1] == "failed"
    assert [m[1] for m in messages] == ["player"]


def test_empty_narration_is_a_failure(services, fake_ai, campaign):
    fake_ai.queue("   ")
    _, events = play(services, campaign["id"], "Espero.")
    assert isinstance(events[-1], TurnFailed) and "vazia" in events[-1].message


def test_client_disconnect_marks_turn_failed(services, fake_ai, campaign):
    fake_ai.queue("Um texto bem longo que não vai ser lido até o fim.")
    prepared = services.turns.prepare(services.local_user_id, campaign["id"], str(uuid.uuid4()), "Falo.")
    stream = services.turns.run(prepared)
    next(stream)  # TurnStarted
    next(stream)  # primeiro pedaço
    stream.close()  # o navegador desconectou
    turns, messages, _, _ = stored(services, campaign["id"])
    assert turns[0][1] == "failed" and "interrompida" in turns[0][2]
    assert len(messages) == 1


def test_unexpected_error_is_contained(services, fake_ai, campaign):
    def explode(messages):
        raise RuntimeError("bug")

    fake_ai.queue(explode)
    _, events = play(services, campaign["id"], "Pulo.")
    assert isinstance(events[-1], TurnFailed) and "Erro interno" in events[-1].message
    assert stored(services, campaign["id"])[0][0][1] == "failed"


def test_only_one_turn_at_a_time(services, fake_ai, campaign):
    services.turns.prepare(services.local_user_id, campaign["id"], str(uuid.uuid4()), "Primeira.")
    with pytest.raises(ConflictError, match="em andamento"):
        services.turns.prepare(services.local_user_id, campaign["id"], str(uuid.uuid4()), "Segunda.")


def test_same_turn_id_with_different_text_is_rejected(services, fake_ai, campaign):
    fake_ai.queue("ok")
    turn_id, _ = play(services, campaign["id"], "Texto A")
    with pytest.raises(ConflictError, match="outro texto"):
        services.turns.prepare(services.local_user_id, campaign["id"], turn_id, "Texto B")


def test_turn_id_from_another_campaign_is_rejected(services, fake_ai, campaign):
    other = services.campaigns.create(services.local_user_id, "Outra", None, [])
    fake_ai.queue("ok")
    turn_id, _ = play(services, campaign["id"], "Ação")
    with pytest.raises(ConflictError):
        services.turns.prepare(services.local_user_id, other["id"], turn_id, "Ação")


def test_only_latest_failed_turn_can_be_retried(services, fake_ai, campaign):
    fake_ai.queue(ProviderUnavailableError("off"), "segunda ok")
    failed_id, _ = play(services, campaign["id"], "Primeira")
    play(services, campaign["id"], "Segunda")
    with pytest.raises(ConflictError, match="mais recente"):
        services.turns.prepare(services.local_user_id, campaign["id"], failed_id, "Primeira")


def test_failed_turns_are_left_out_of_ai_history(services, fake_ai, campaign):
    fake_ai.queue(ProviderUnavailableError("off"), "Narração B.", "Narração C.")
    play(services, campaign["id"], "Ação A")
    play(services, campaign["id"], "Ação B")
    play(services, campaign["id"], "Ação C")
    sent = [(m.role, m.content) for m in fake_ai.calls[2].messages[1:]]
    assert sent == [("user", "Ação B"), ("assistant", "Narração B."), ("user", "Ação C")]


@pytest.mark.parametrize(
    "turn_id,text,error",
    [("nao-e-uuid", "oi", InvalidInputError), (str(uuid.uuid4()), "   ", InvalidInputError),
     (str(uuid.uuid4()), "x" * 4001, InvalidInputError)],
)
def test_invalid_input(services, campaign, turn_id, text, error):
    with pytest.raises(error):
        services.turns.prepare(services.local_user_id, campaign["id"], turn_id, text)


def test_unknown_campaign(services):
    with pytest.raises(NotFoundError):
        services.turns.prepare(services.local_user_id, str(uuid.uuid4()), str(uuid.uuid4()), "oi")


def test_turn_left_processing_becomes_failed_on_restart(flask_app, services, campaign, settings):
    services.turns.prepare(services.local_user_id, campaign["id"], str(uuid.uuid4()), "Fecho o programa.")
    services.db.dispose()
    restarted = initialize_services(flask_app, settings)
    with restarted.db.transaction() as session:
        turn = CampaignData(session, campaign["id"]).turns.list_ordered()[0]
        assert turn.status == Turn.STATUS_FAILED and "fechado" in turn.error
    restarted.db.dispose()
