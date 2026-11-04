"""Interface comum a todos os provedores de IA."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Literal

from app.providers.errors import ProviderResponseError

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class GenerationOptions:
    model: str
    temperature: float | None = None
    max_output_tokens: int | None = None
    # Tamanho da "memória de trabalho" do modelo em tokens (no Ollama: num_ctx).
    context_window: int | None = None
    timeout_seconds: float = 600.0
    # Esquema JSON que a resposta deve seguir (provedores que suportam usam para forçar o formato).
    json_schema: dict | None = None


@dataclass(frozen=True)
class CompletionResult:
    text: str
    provider: str
    model: str
    tokens_in: int | None  # None quando o provedor não informa (nunca inventado)
    tokens_out: int | None
    duration_ms: int


@dataclass(frozen=True)
class TextDelta:
    """Um pedaço de texto que acabou de chegar."""

    text: str


@dataclass(frozen=True)
class StreamCompleted:
    """Último evento de um stream: o resultado completo, com uso de tokens."""

    result: CompletionResult


StreamEvent = TextDelta | StreamCompleted


class AIProvider(ABC):
    name: str = "base"
    # Serviço pago? O sistema avisa antes de usar e respeita o limite de gasto (SPEC 17.3).
    is_paid: bool = False
    # Aviso sobre o que o provedor aceita em temas adultos (D-007); vazio = sem observação.
    content_note: str = ""

    @abstractmethod
    def stream(self, messages: Sequence[ChatMessage], options: GenerationOptions) -> Iterator[StreamEvent]:
        """Gera a resposta aos poucos: vários TextDelta e, no fim, um StreamCompleted."""

    def complete(self, messages: Sequence[ChatMessage], options: GenerationOptions) -> CompletionResult:
        """Gera a resposta inteira de uma vez."""
        for event in self.stream(messages, options):
            if isinstance(event, StreamCompleted):
                return event.result
        raise ProviderResponseError("A resposta da IA terminou sem ser concluída.")

    def list_models(self) -> list[str]:
        """Modelos disponíveis neste provedor (vazio se o provedor não informa)."""
        return []
