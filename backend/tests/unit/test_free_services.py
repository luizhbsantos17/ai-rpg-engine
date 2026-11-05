"""Serviços gratuitos (Gemini, Groq, OpenRouter) com servidor SIMULADO (httpx.MockTransport).

NÃO é integração real: sem chave do dono, nada aqui fala com os serviços de verdade.
"""

import json

import httpx
import pytest

from app.config import ConfigError, load_settings
from app.providers import ChatMessage, GenerationOptions, ProviderResponseError, ProviderUnavailableError
from app.providers.free_services import FREE_SERVICES
from app.providers.openai_compat import OpenAICompatProvider, RateLimitedError
from app.providers.registry import build_provider, resolve_model

MESSAGES = [ChatMessage("user", "Responda em JSON.")]
SCHEMA = {"type": "object", "properties": {"intent": {"type": "string"}}}


def ok(text="{}"):
    body = {"choices": [{"index": 0, "delta": {"content": text}, "finish_reason": "stop"}]}
    return httpx.Response(200, text=f"data: {json.dumps(body)}\n\ndata: [DONE]\n\n")


def provider(name, handler):
    service = FREE_SERVICES[name]
    p = OpenAICompatProvider(service.base_url, "chave", paid=False, transport=httpx.MockTransport(handler),
                             service=service)
    p.waits = []
    p._sleep = p.waits.append  # não espera de verdade
    return p


def test_rate_limit_waits_and_tries_again_before_any_text():
    answers = [httpx.Response(429, headers={"retry-after": "7"}, json={"error": "devagar"}), ok("oi")]
    p = provider("groq", lambda request: answers.pop(0))
    result = p.complete(MESSAGES, GenerationOptions(model="qwen/qwen3.8-27b"))
    assert result.text == "oi" and p.waits == [7.0]


def test_rate_limit_gives_up_after_a_few_waits():
    p = provider("groq", lambda request: httpx.Response(429, json={"error": "devagar"}))
    with pytest.raises(RateLimitedError):
        p.complete(MESSAGES, GenerationOptions(model="qwen/qwen3.8-27b"))
    assert p.waits == [5.0, 10.0, 15.0]


def test_json_falls_back_when_the_model_does_not_accept_the_schema_and_remembers():
    formats = []

    def handler(request):
        body = json.loads(request.content)
        formats.append((body.get("response_format") or {}).get("type"))
        if formats[-1] == "json_schema":
            return httpx.Response(400, json={"error": {"message": "json_schema not supported"}})
        return ok('{"intent": "x"}')

    p = provider("openrouter", handler)
    options = GenerationOptions(model="google/gemma-4-31b-it:free", json_schema=SCHEMA)
    assert p.complete(MESSAGES, options).text == '{"intent": "x"}'
    p.complete(MESSAGES, options)
    assert formats == ["json_schema", "json_object", "json_object"]  # na segunda vez já vai direto


def test_openrouter_only_uses_free_models():
    seen = {}

    def handler(request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "openai/gpt-pago"}, {"id": "x/outro:free"},
                                                      {"id": "google/gemma-4-31b-it:free"}]})
        seen["title"] = request.headers.get("x-title")
        return ok()

    p = provider("openrouter", handler)
    assert p.list_models() == ["x/outro:free", "google/gemma-4-31b-it:free"]
    assert resolve_model(p, None) == "google/gemma-4-31b-it:free"  # o preferido, quando existe
    with pytest.raises(ProviderResponseError, match="bloqueado"):
        p.complete(MESSAGES, GenerationOptions(model="openai/gpt-pago"))
    p.complete(MESSAGES, GenerationOptions(model="x/outro:free"))
    assert seen["title"] == "AI RPG Engine"


def test_gemini_model_names_and_choice():
    p = provider("gemini", lambda request: httpx.Response(200, json={"data": [
        {"id": "models/gemini-embedding-001"}, {"id": "models/gemini-2.5-flash-image"},
        {"id": "models/gemini-2.5-flash"}]}))
    assert resolve_model(p, None) == "gemini-2.5-flash"  # sem o prefixo "models/", sem modelos de imagem/vetor
    assert p.name == "gemini" and "Gemini" in p.content_note


def test_groq_asks_gpt_oss_to_think_less():
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return ok()

    p = provider("groq", handler)
    p.complete(MESSAGES, GenerationOptions(model="openai/gpt-oss-120b"))
    p.complete(MESSAGES, GenerationOptions(model="qwen/qwen3.8-27b"))
    assert bodies[0]["reasoning_effort"] == "low" and "reasoning_effort" not in bodies[1]


def settings(**environ):
    return load_settings(environ=environ, env_file=None)


def test_config_requires_the_key_and_blocks_paid_openrouter_models():
    with pytest.raises(ConfigError, match="aistudio.google.com"):
        settings(AI_PROVIDER="gemini")
    with pytest.raises(ConfigError, match="gratuito"):
        settings(AI_PROVIDER="openrouter", OPENROUTER_API_KEY="k", AI_MODEL="openai/gpt-5")
    built = build_provider(settings(AI_PROVIDER="groq", GROQ_API_KEY="segredo"))
    assert built.name == "groq" and built.is_paid is False and "segredo" not in repr(built)
    assert "segredo" not in repr(settings(AI_PROVIDER="groq", GROQ_API_KEY="segredo"))


def test_busy_model_falls_back_to_the_next_recommended_and_sticks():
    asked = []

    def handler(request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "models/gemini-3.5-flash"},
                                                      {"id": "models/gemini-3.6-flash"}]})
        body = json.loads(request.content)
        asked.append((body["model"], body.get("reasoning_effort")))
        if body["model"] == "gemini-3.5-flash":
            return httpx.Response(503, json=[{"error": {"message": "high demand"}}])  # formato do Gemini: lista
        return ok("A taverna ferve.")

    p = provider("gemini", handler)
    p.auto_fallback = True
    model = resolve_model(p, None)
    assert model == "gemini-3.5-flash"
    assert p.complete(MESSAGES, GenerationOptions(model=model)).text == "A taverna ferve."
    assert asked == [("gemini-3.5-flash", "none"), ("gemini-3.5-flash", "none"), ("gemini-3.6-flash", "none")]
    assert p.waits == [5.0]  # com outro modelo disponível, espera uma vez só
    assert resolve_model(p, None) == "gemini-3.6-flash"  # passa a usar o que respondeu


def test_without_auto_choice_there_is_no_fallback_and_the_error_is_readable():
    p = provider("gemini", lambda request: httpx.Response(503, json=[{"error": {"message": "high demand"}}]))
    with pytest.raises(ProviderUnavailableError, match="sobrecarregado.*high demand"):
        p.complete(MESSAGES, GenerationOptions(model="gemini-3.5-flash"))


def test_daily_quota_skips_waiting_and_goes_to_the_next_model():
    daily = [{"error": {"message": "Generate content requests per day limit exceeded on Free Tier",
                        "details": [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "26754s"}]}}]

    def handler(request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "gemini-3.5-flash"}, {"id": "gemini-3.6-flash"}]})
        if json.loads(request.content)["model"] == "gemini-3.5-flash":
            return httpx.Response(429, json=daily)
        return ok("ok")

    p = provider("gemini", handler)
    p.auto_fallback = True
    assert p.complete(MESSAGES, GenerationOptions(model="gemini-3.5-flash")).text == "ok"
    assert p.waits == []  # não espera 7 horas nem 5 s à toa
