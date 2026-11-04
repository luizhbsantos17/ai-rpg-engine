r"""Serviço gratuito DE VERDADE (Gemini, Groq ou OpenRouter), com a chave do .env do dono.

Só roda com AI_PROVIDER=gemini|groq|openrouter e a chave preenchida; senão, é pulado (nunca inventado).
Gasta 2 pedidos do limite gratuito diário.
    .\.venv\Scripts\python.exe -m pytest -m external -s tests/external/test_free_service_real.py
"""

import json

import pytest

from app.config import FREE_SERVICE_KEYS, ConfigError, load_settings
from app.providers import ChatMessage, GenerationOptions
from app.providers.registry import build_provider, resolve_model

pytestmark = pytest.mark.external


@pytest.fixture
def provider_and_model():
    try:
        settings = load_settings()
    except ConfigError as exc:
        pytest.skip(f"Configuração do .env incompleta: {exc}")
    if settings.ai_provider not in FREE_SERVICE_KEYS:
        pytest.skip("AI_PROVIDER no .env não é um serviço gratuito na internet (gemini, groq ou openrouter).")
    provider = build_provider(settings)
    return provider, resolve_model(provider, settings.ai_model)


def test_narrates_in_portuguese(provider_and_model):
    provider, model = provider_and_model
    result = provider.complete([ChatMessage("system", "Você narra um RPG em português do Brasil."),
                                ChatMessage("user", "Descreva em 2 frases uma taverna à noite.")],
                               GenerationOptions(model=model, max_output_tokens=200))
    print(f"\n{provider.name} {result.model} tokens={result.tokens_in}/{result.tokens_out} "
          f"{result.duration_ms} ms\n{result.text}")
    assert result.text.strip()


def test_returns_valid_json(provider_and_model):
    provider, model = provider_and_model
    schema = {"type": "object", "properties": {"intent": {"type": "string"}, "operations": {"type": "array"}},
              "required": ["intent", "operations"]}
    result = provider.complete([ChatMessage("user", 'Ação: "abro a porta". Responda só com JSON: '
                                                    '{"intent": "...", "operations": []}')],
                               GenerationOptions(model=model, max_output_tokens=300, json_schema=schema))
    print(f"\nJSON ({provider._json_mode.get(model)}): {result.text!r}")
    data = json.loads(result.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```"))
    assert isinstance(data["intent"], str)
