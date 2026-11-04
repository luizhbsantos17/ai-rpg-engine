"""Escolhe o provedor e o modelo a partir da configuração."""

from __future__ import annotations

from app.config import Settings
from app.providers.base import AIProvider, GenerationOptions
from app.providers.errors import ModelNotFoundError
from app.providers.ollama import OllamaProvider


def build_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider == "ollama":
        return OllamaProvider(settings.ollama_base_url)
    if settings.ai_provider == "fake":
        from app.providers.fake import FakeProvider

        return FakeProvider()
    raise ValueError(f"Provedor desconhecido: {settings.ai_provider}")


def resolve_model(provider: AIProvider, configured_model: str | None) -> str:
    """Modelo configurado em AI_MODEL ou, se vazio, o primeiro instalado no provedor."""
    if configured_model:
        return configured_model
    models = provider.list_models()
    if not models:
        raise ModelNotFoundError(
            "Nenhum modelo de IA instalado. No Ollama, instale um com: ollama pull <nome-do-modelo>"
        )
    return models[0]


def generation_options(settings: Settings, model: str) -> GenerationOptions:
    return GenerationOptions(
        model=model,
        temperature=settings.ai_temperature,
        max_output_tokens=settings.ai_max_output_tokens,
        context_window=settings.ai_context_window,
        timeout_seconds=settings.ai_timeout_seconds,
    )
