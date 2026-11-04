r"""Adaptador no formato OpenAI contra um servidor DE VERDADE: o Ollama local em /v1 (gratuito).

Como rodar (com o Ollama aberto e ao menos um modelo instalado):
    .\.venv\Scripts\python.exe -m pytest -m external -s
"""

import json

import pytest

from app.config import load_settings
from app.providers import ChatMessage, GenerationOptions, ProviderUnavailableError, TextDelta
from app.providers.ollama import OllamaProvider
from app.providers.openai_compat import OpenAICompatProvider
from app.providers.registry import resolve_model

pytestmark = pytest.mark.external


@pytest.fixture
def provider_and_model():
    settings = load_settings()
    try:
        model = resolve_model(OllamaProvider(settings.ollama_base_url), settings.ai_model)
    except ProviderUnavailableError as exc:
        pytest.fail(f"Ollama não está acessível: {exc}")
    return OpenAICompatProvider(settings.ollama_base_url.rstrip("/") + "/v1", None, paid=False), model


def test_streams_text_with_usage(provider_and_model):
    provider, model = provider_and_model
    events = list(provider.stream([ChatMessage("user", "Responda apenas com a palavra: pronto")],
                                  GenerationOptions(model=model, max_output_tokens=20)))
    result = events[-1].result
    print(f"\nmodelo={result.model} tokens_in={result.tokens_in} tokens_out={result.tokens_out} "
          f"pedaços={sum(isinstance(e, TextDelta) for e in events)} duracao_ms={result.duration_ms} "
          f"texto={result.text!r}")
    assert result.text.strip()
    assert model in provider.list_models()


def test_json_schema_is_followed(provider_and_model):
    provider, model = provider_and_model
    schema = {"type": "object", "properties": {"cor": {"type": "string"}, "numero": {"type": "integer"}},
              "required": ["cor", "numero"]}
    result = provider.complete([ChatMessage("user", "Invente uma cor e um número. Responda em JSON.")],
                               GenerationOptions(model=model, max_output_tokens=60, json_schema=schema))
    print(f"\nJSON: {result.text!r}")
    data = json.loads(result.text)
    assert isinstance(data["cor"], str) and isinstance(data["numero"], int)
