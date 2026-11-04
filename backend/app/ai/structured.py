"""Respostas estruturadas (JSON) da IA, com validação e reenvio do erro (D-008).

A IA é tratada como não confiável: a resposta é conferida com um esquema Pydantic.
Se vier inválida, o erro é mostrado a ela e o pedido é repetido (até `max_attempts`).
Cada tentativa fica registrada para auditoria (ai_requests).
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

from app.providers import AIProvider, ChatMessage, CompletionResult, GenerationOptions

ModelT = TypeVar("ModelT", bound=BaseModel)
MAX_ERROR_CHARS = 600
_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


@dataclass(frozen=True)
class Attempt:
    result: CompletionResult
    error: str | None  # None = resposta válida


@dataclass
class StructuredResult(Generic[ModelT]):
    value: ModelT | None
    attempts: list[Attempt] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.value is not None


def parse_json_response(text: str, schema: type[ModelT]) -> ModelT:
    """Extrai e valida o JSON. Aceita a resposta dentro de ```json ... ``` (comum em modelos)."""
    cleaned = text.strip()
    fenced = _FENCE.match(cleaned)
    if fenced:
        cleaned = fenced.group(1)
    data = json.loads(cleaned)
    return schema.model_validate(data)


def describe_error(exc: Exception) -> str:
    if isinstance(exc, json.JSONDecodeError):
        return f"A resposta não é JSON válido ({exc.msg}, posição {exc.pos})."
    if isinstance(exc, ValidationError):
        parts = [f"{'.'.join(map(str, e['loc'])) or 'raiz'}: {e['msg']}" for e in exc.errors()[:5]]
        return "O JSON não segue o formato pedido: " + "; ".join(parts)
    return str(exc)


def request_structured(
    provider: AIProvider,
    messages: Sequence[ChatMessage],
    options: GenerationOptions,
    schema: type[ModelT],
    max_attempts: int = 2,
) -> StructuredResult[ModelT]:
    """Pede uma resposta no formato `schema`. Erros do provedor (conexão etc.) sobem como exceção."""
    conversation = list(messages)
    options = replace(options, json_schema=schema.model_json_schema())
    outcome: StructuredResult[ModelT] = StructuredResult(None)
    for _ in range(max(1, max_attempts)):
        result = provider.complete(conversation, options)
        try:
            outcome.value = parse_json_response(result.text, schema)
        except (json.JSONDecodeError, ValidationError) as exc:
            error = describe_error(exc)[:MAX_ERROR_CHARS]
            outcome.attempts.append(Attempt(result, error))
            conversation += [
                ChatMessage("assistant", result.text[:4000]),
                ChatMessage("user", f"{error} Responda de novo, somente com o JSON no formato pedido."),
            ]
            continue
        outcome.attempts.append(Attempt(result, None))
        return outcome
    return outcome
