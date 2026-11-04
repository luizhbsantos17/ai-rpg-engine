r"""Teste com o Ollama DE VERDADE (integração real). Não roda por padrão.

Como rodar (com o Ollama aberto e ao menos um modelo instalado):
    .\.venv\Scripts\python.exe -m pytest -m external
"""

import pytest

from app.config import load_settings
from app.providers import ChatMessage, ProviderUnavailableError
from app.providers.ollama import OllamaProvider
from app.providers.registry import generation_options, resolve_model

pytestmark = pytest.mark.external


@pytest.fixture
def provider_and_model():
    settings = load_settings()
    provider = OllamaProvider(settings.ollama_base_url)
    try:
        model = resolve_model(provider, settings.ai_model)
    except ProviderUnavailableError as exc:
        pytest.fail(f"Ollama não está acessível: {exc}")
    return provider, model, settings


def test_real_ollama_answers(provider_and_model):
    provider, model, settings = provider_and_model
    options = generation_options(settings, model)
    messages = [ChatMessage("user", "Responda apenas com a palavra: pronto")]
    result = provider.complete(messages, options)
    print(f"\nmodelo={result.model} tokens_in={result.tokens_in} tokens_out={result.tokens_out} "
          f"duracao_ms={result.duration_ms} texto={result.text!r}")
    assert result.text.strip()
    assert result.tokens_out and result.tokens_out > 0
