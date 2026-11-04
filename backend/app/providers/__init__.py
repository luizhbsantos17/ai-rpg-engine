"""Camada de provedores de IA: o resto do sistema não sabe qual IA está sendo usada.

Trocar de provedor (Ollama, serviço externo...) não exige mexer no motor (SPEC 17.2).
"""

from app.providers.base import (
    AIProvider,
    ChatMessage,
    CompletionResult,
    GenerationOptions,
    StreamCompleted,
    StreamEvent,
    TextDelta,
)
from app.providers.errors import (
    ModelNotFoundError,
    ProviderError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

__all__ = [
    "AIProvider",
    "ChatMessage",
    "CompletionResult",
    "GenerationOptions",
    "ModelNotFoundError",
    "ProviderError",
    "ProviderResponseError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
    "StreamCompleted",
    "StreamEvent",
    "TextDelta",
]
