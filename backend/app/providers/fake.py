"""FakeProvider: respostas roteirizadas, SÓ para testes automatizados.

Verifica a lógica interna sem internet e sem custo. Não é uma integração real com IA
(SPEC Parte 22) e o programa recusa usá-lo fora de APP_ENV=test.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass

from app.providers.base import (
    AIProvider,
    ChatMessage,
    CompletionResult,
    GenerationOptions,
    StreamCompleted,
    StreamEvent,
    TextDelta,
)
from app.providers.errors import ProviderError


@dataclass(frozen=True)
class FailMidStream:
    """Roteiro: entrega `partial_text` e então falha com `error` (simula queda no meio)."""

    partial_text: str
    error: ProviderError


ScriptItem = str | ProviderError | FailMidStream | Callable[[Sequence[ChatMessage]], str]


@dataclass(frozen=True)
class FakeCall:
    messages: tuple[ChatMessage, ...]
    options: GenerationOptions


class FakeProvider(AIProvider):
    name = "fake"

    def __init__(self, script: Sequence[ScriptItem] = (), chunk_size: int = 8, default: ScriptItem | None = None):
        self._script = list(script)
        self.chunk_size = chunk_size
        self.default = default
        self.calls: list[FakeCall] = []

    def queue(self, *items: ScriptItem) -> None:
        self._script.extend(items)

    def _next_item(self, messages: Sequence[ChatMessage]) -> ScriptItem:
        if self._script:
            return self._script.pop(0)
        if self.default is not None:
            return self.default
        raise AssertionError("FakeProvider: nenhuma resposta roteirizada restante.")

    def stream(self, messages: Sequence[ChatMessage], options: GenerationOptions) -> Iterator[StreamEvent]:
        self.calls.append(FakeCall(tuple(messages), options))
        item = self._next_item(messages)
        if isinstance(item, ProviderError):
            raise item
        if isinstance(item, FailMidStream):
            yield from self._chunks(item.partial_text)
            raise item.error
        text = item(messages) if callable(item) else item
        yield from self._chunks(text)
        yield StreamCompleted(
            CompletionResult(
                text=text,
                provider=self.name,
                model=options.model,
                tokens_in=sum(len(m.content.split()) for m in messages),
                tokens_out=len(text.split()),
                duration_ms=0,
            )
        )

    def _chunks(self, text: str) -> Iterator[TextDelta]:
        for start in range(0, len(text), self.chunk_size):
            yield TextDelta(text[start : start + self.chunk_size])

    def list_models(self) -> list[str]:
        return ["fake-model"]
