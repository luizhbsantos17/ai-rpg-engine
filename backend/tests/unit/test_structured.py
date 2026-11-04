from pydantic import BaseModel

from app.ai.structured import parse_json_response, request_structured
from app.providers import ChatMessage, GenerationOptions
from app.providers.fake import FakeProvider
from app.providers.ollama import OllamaProvider


class Answer(BaseModel):
    intent: str
    operations: list[dict] = []


OPTIONS = GenerationOptions(model="m")
MESSAGES = [ChatMessage("user", "faça algo")]


def test_valid_json_on_first_try():
    provider = FakeProvider(['{"intent": "olhar", "operations": []}'])
    result = request_structured(provider, MESSAGES, OPTIONS, Answer)
    assert result.ok and result.value.intent == "olhar"
    assert len(result.attempts) == 1 and result.attempts[0].error is None
    # O esquema JSON é enviado ao provedor (para forçar o formato no Ollama).
    assert provider.calls[0].options.json_schema["title"] == "Answer"


def test_invalid_json_is_sent_back_with_the_error_and_retried():
    provider = FakeProvider(["isto não é json", '{"intent": "corrigido"}'])
    result = request_structured(provider, MESSAGES, OPTIONS, Answer, max_attempts=2)
    assert result.ok and result.value.intent == "corrigido"
    assert result.attempts[0].error.startswith("A resposta não é JSON válido")
    retry_messages = provider.calls[1].messages
    assert retry_messages[-2].content == "isto não é json"
    assert "não é JSON válido" in retry_messages[-1].content


def test_wrong_shape_is_retried_then_given_up():
    provider = FakeProvider(['{"operations": []}', '{"intent": 5}'])
    result = request_structured(provider, MESSAGES, OPTIONS, Answer, max_attempts=2)
    assert not result.ok
    assert [a.error is not None for a in result.attempts] == [True, True]
    assert "intent" in result.attempts[0].error


def test_json_inside_markdown_fence_is_accepted():
    assert parse_json_response('```json\n{"intent": "x"}\n```', Answer).intent == "x"


def test_ollama_payload_includes_format_schema():
    payload = OllamaProvider._payload(MESSAGES, GenerationOptions(model="m", json_schema={"type": "object"}))
    assert payload["format"] == {"type": "object"}
