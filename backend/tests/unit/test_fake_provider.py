import pytest

from app.providers import (
    ChatMessage,
    GenerationOptions,
    ProviderResponseError,
    ProviderUnavailableError,
    StreamCompleted,
    TextDelta,
)
from app.providers.fake import FailMidStream, FakeProvider

MESSAGES = [ChatMessage("user", "olá mundo")]
OPTIONS = GenerationOptions(model="m")


def test_stream_delivers_pieces_then_completed():
    provider = FakeProvider(["Era uma vez um reino."], chunk_size=5)
    events = list(provider.stream(MESSAGES, OPTIONS))
    deltas = [e.text for e in events if isinstance(e, TextDelta)]
    assert "".join(deltas) == "Era uma vez um reino."
    assert len(deltas) > 1
    assert isinstance(events[-1], StreamCompleted)
    assert events[-1].result.text == "Era uma vez um reino."
    assert events[-1].result.model == "m"


def test_complete_returns_full_text_and_records_calls():
    provider = FakeProvider(["um", "dois"])
    assert provider.complete(MESSAGES, OPTIONS).text == "um"
    assert provider.complete(MESSAGES, OPTIONS).text == "dois"
    assert len(provider.calls) == 2
    assert provider.calls[0].messages == tuple(MESSAGES)


def test_scripted_error_is_raised():
    provider = FakeProvider([ProviderUnavailableError("desligado")])
    with pytest.raises(ProviderUnavailableError):
        provider.complete(MESSAGES, OPTIONS)


def test_failure_in_the_middle_of_stream():
    provider = FakeProvider([FailMidStream("começo", ProviderResponseError("caiu"))])
    received = []
    with pytest.raises(ProviderResponseError):
        for event in provider.stream(MESSAGES, OPTIONS):
            received.append(event)
    assert "".join(e.text for e in received) == "começo"


def test_callable_script_sees_messages():
    provider = FakeProvider([lambda messages: f"eco: {messages[-1].content}"])
    assert provider.complete(MESSAGES, OPTIONS).text == "eco: olá mundo"


def test_running_out_of_script_is_a_test_error():
    with pytest.raises(AssertionError):
        FakeProvider().complete(MESSAGES, OPTIONS)
