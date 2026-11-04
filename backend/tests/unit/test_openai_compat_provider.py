"""Adaptador no formato OpenAI com um servidor SIMULADO (httpx.MockTransport). NÃO é integração real.

O teste com um servidor de verdade (o Ollama em /v1, gratuito) está em tests/external/.
"""

import json

import httpx
import pytest

from app.config import ConfigError, load_settings
from app.providers import (
    ChatMessage,
    GenerationOptions,
    ModelNotFoundError,
    ProviderResponseError,
    ProviderUnavailableError,
    StreamCompleted,
    TextDelta,
)
from app.providers.openai_compat import OpenAICompatProvider, RateLimitedError
from app.providers.registry import build_provider

MESSAGES = [ChatMessage("system", "Você narra."), ChatMessage("user", "Abro a porta.")]
OPTIONS = GenerationOptions(model="modelo-y", temperature=0.5, max_output_tokens=300, context_window=4096)


def sse(*events):
    return "".join(f"data: {e if isinstance(e, str) else json.dumps(e)}\n\n" for e in events)


def chunk(text=None, finish=None, usage=None):
    choices = [{"index": 0, "delta": {"content": text} if text else {}, "finish_reason": finish}]
    body = {"model": "modelo-y", "choices": choices if (text or finish) else []}
    if usage:
        body["usage"] = usage
    return body


def provider_with(handler, key="chave-secreta"):
    return OpenAICompatProvider("http://ia.test/v1/", key, paid=False, transport=httpx.MockTransport(handler))


def test_request_format_and_stream():
    seen = {}

    def handler(request):
        seen["url"], seen["auth"] = str(request.url), request.headers.get("authorization")
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, text=": ping\n\n" + sse(
            chunk("A porta "), chunk("range."), chunk(finish="stop"),
            chunk(usage={"prompt_tokens": 42, "completion_tokens": 7}), "[DONE]"))

    events = list(provider_with(handler).stream(MESSAGES, OPTIONS))
    assert seen["url"] == "http://ia.test/v1/chat/completions"
    assert seen["auth"] == "Bearer chave-secreta"
    assert seen["body"]["messages"][1] == {"role": "user", "content": "Abro a porta."}
    assert seen["body"]["max_tokens"] == 300 and seen["body"]["temperature"] == 0.5
    assert seen["body"]["stream"] is True and "num_ctx" not in json.dumps(seen["body"])
    assert [e.text for e in events if isinstance(e, TextDelta)] == ["A porta ", "range."]
    result = events[-1].result
    assert isinstance(events[-1], StreamCompleted)
    assert (result.text, result.tokens_in, result.tokens_out, result.provider) == ("A porta range.", 42, 7, "openai_compat")


def test_json_schema_and_no_key():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, text=sse(chunk("{}", finish="stop")))  # sem [DONE]: finish_reason basta

    schema = {"type": "object", "properties": {"intent": {"type": "string"}}}
    result = provider_with(handler, key=None).complete(MESSAGES, GenerationOptions(model="m", json_schema=schema))
    assert seen["auth"] is None
    assert seen["body"]["response_format"]["json_schema"]["schema"] == schema
    assert result.text == "{}" and result.tokens_in is None  # sem contagem informada: nunca inventada


@pytest.mark.parametrize("status, error, kind, words", [
    (401, {"error": {"message": "bad key"}}, ProviderResponseError, "chave"),
    (404, {"error": {"message": "model not found"}}, ModelNotFoundError, "modelo-y"),
    (429, {"error": "slow down"}, RateLimitedError, "esperar"),
    (500, {"error": {"message": "boom"}}, ProviderResponseError, "500"),
])
def test_http_errors(status, error, kind, words):
    provider = provider_with(lambda request: httpx.Response(status, json=error))
    with pytest.raises(kind, match=words):
        list(provider.stream(MESSAGES, OPTIONS))


def test_error_event_and_cut_stream():
    with pytest.raises(ProviderResponseError, match="informou um erro"):
        list(provider_with(lambda r: httpx.Response(200, text=sse({"error": {"message": "sobrecarga"}}))).stream(
            MESSAGES, OPTIONS))
    with pytest.raises(ProviderResponseError, match="interrompida"):
        list(provider_with(lambda r: httpx.Response(200, text=sse(chunk("meio")))).stream(MESSAGES, OPTIONS))
    with pytest.raises(ProviderResponseError, match="não é JSON"):
        list(provider_with(lambda r: httpx.Response(200, text="data: {quebrado\n\n")).stream(MESSAGES, OPTIONS))


def test_connection_refused():
    def handler(request):
        raise httpx.ConnectError("recusado", request=request)

    with pytest.raises(ProviderUnavailableError):
        list(provider_with(handler).stream(MESSAGES, OPTIONS))


def test_list_models_and_key_never_in_repr():
    provider = provider_with(lambda r: httpx.Response(200, json={"data": [{"id": "a"}, {"id": "b"}]}))
    assert provider.list_models() == ["a", "b"]
    assert "chave-secreta" not in repr(provider)


def settings(**extra):
    return load_settings(environ={"AI_PROVIDER": "openai_compat", **extra}, env_file=None)


def test_paid_services_are_blocked_until_spend_control_exists():
    with pytest.raises(ConfigError, match="BASE_URL"):
        settings()
    with pytest.raises(ConfigError, match="pagos ainda estão bloqueados"):
        settings(OPENAI_COMPAT_BASE_URL="https://api.exemplo.com/v1")  # padrão: considerado pago
    free = settings(OPENAI_COMPAT_BASE_URL="http://localhost:1234/v1", OPENAI_COMPAT_PAID="false")
    provider = build_provider(free)
    assert isinstance(provider, OpenAICompatProvider) and provider.is_paid is False
