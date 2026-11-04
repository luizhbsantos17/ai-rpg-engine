"""Testes do adaptador do Ollama com um servidor SIMULADO (httpx.MockTransport).

Verificam o formato do pedido e o tratamento das respostas. NÃO são integração real:
o teste com o Ollama de verdade está em tests/external/ (marcador `external`).
"""

import json

import httpx
import pytest

from app.providers import (
    ChatMessage,
    GenerationOptions,
    ModelNotFoundError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    StreamCompleted,
    TextDelta,
)
from app.providers.ollama import OllamaProvider

MESSAGES = [ChatMessage("system", "Você narra."), ChatMessage("user", "Abro a porta.")]
OPTIONS = GenerationOptions(model="modelo-x", temperature=0.7, max_output_tokens=200, context_window=4096)


def ndjson(*objects):
    return "\n".join(json.dumps(o) for o in objects) + "\n"


def provider_with(handler):
    return OllamaProvider("http://ollama.test:11434/", transport=httpx.MockTransport(handler))


def ok_stream(request):
    return httpx.Response(
        200,
        text=ndjson(
            {"model": "modelo-x", "message": {"role": "assistant", "content": "A porta "}, "done": False},
            {"model": "modelo-x", "message": {"role": "assistant", "content": "range."}, "done": False},
            {"model": "modelo-x", "message": {"role": "assistant", "content": ""}, "done": True,
             "prompt_eval_count": 31, "eval_count": 4},
        ),
    )


def test_request_format():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return ok_stream(request)

    provider_with(handler).complete(MESSAGES, OPTIONS)
    assert seen["url"] == "http://ollama.test:11434/api/chat"
    assert seen["body"] == {
        "model": "modelo-x",
        "messages": [{"role": "system", "content": "Você narra."}, {"role": "user", "content": "Abro a porta."}],
        "stream": True,
        "options": {"temperature": 0.7, "num_predict": 200, "num_ctx": 4096},
    }


def test_stream_pieces_and_usage():
    events = list(provider_with(ok_stream).stream(MESSAGES, OPTIONS))
    assert [e.text for e in events if isinstance(e, TextDelta)] == ["A porta ", "range."]
    result = events[-1].result
    assert isinstance(events[-1], StreamCompleted)
    assert (result.text, result.tokens_in, result.tokens_out) == ("A porta range.", 31, 4)
    assert result.provider == "ollama"


def test_missing_model_gives_clear_error():
    provider = provider_with(lambda r: httpx.Response(404, json={"error": "model 'modelo-x' not found"}))
    with pytest.raises(ModelNotFoundError, match="ollama pull modelo-x"):
        provider.complete(MESSAGES, OPTIONS)


def test_server_error_status():
    provider = provider_with(lambda r: httpx.Response(500, json={"error": "sem memória"}))
    with pytest.raises(ProviderResponseError, match="500.*sem memória"):
        provider.complete(MESSAGES, OPTIONS)


def test_error_line_in_the_middle_of_stream():
    body = ndjson({"message": {"content": "Era"}, "done": False}, {"error": "falha interna"})
    provider = provider_with(lambda r: httpx.Response(200, text=body))
    with pytest.raises(ProviderResponseError, match="falha interna"):
        list(provider.stream(MESSAGES, OPTIONS))


def test_stream_ending_without_done_is_an_error():
    body = ndjson({"message": {"content": "Era"}, "done": False})
    provider = provider_with(lambda r: httpx.Response(200, text=body))
    with pytest.raises(ProviderResponseError, match="interrompida"):
        list(provider.stream(MESSAGES, OPTIONS))


def test_invalid_json_line():
    provider = provider_with(lambda r: httpx.Response(200, text="isto não é json\n"))
    with pytest.raises(ProviderResponseError, match="não é JSON"):
        list(provider.stream(MESSAGES, OPTIONS))


def test_connection_refused():
    def handler(request):
        raise httpx.ConnectError("recusado", request=request)

    with pytest.raises(ProviderUnavailableError, match="instalado e aberto"):
        provider_with(handler).complete(MESSAGES, OPTIONS)


def test_timeout():
    def handler(request):
        raise httpx.ReadTimeout("lento", request=request)

    with pytest.raises(ProviderTimeoutError):
        provider_with(handler).complete(MESSAGES, OPTIONS)


def test_list_models():
    body = {"models": [{"name": "llama-a:1b"}, {"name": "qwen-b:0.5b"}]}
    provider = provider_with(lambda r: httpx.Response(200, json=body))
    assert provider.list_models() == ["llama-a:1b", "qwen-b:0.5b"]


def test_options_are_omitted_when_not_set():
    payload = OllamaProvider._payload(MESSAGES, GenerationOptions(model="m"))
    assert "options" not in payload
