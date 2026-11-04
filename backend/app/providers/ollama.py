"""Adaptador do Ollama (servidor de modelos de IA local e gratuito).

Documentação da API usada: POST /api/chat (respostas em linhas JSON quando
"stream": true) e GET /api/tags (modelos instalados).
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator, Sequence
from typing import Any

import httpx

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

CONNECT_TIMEOUT_SECONDS = 5.0


class OllamaProvider(AIProvider):
    name = "ollama"
    is_paid = False

    def __init__(self, base_url: str, transport: httpx.BaseTransport | None = None):
        self.base_url = base_url.rstrip("/")
        self._transport = transport  # usado pelos testes para simular o servidor

    def _client(self, timeout_seconds: float) -> httpx.Client:
        timeout = httpx.Timeout(timeout_seconds, connect=CONNECT_TIMEOUT_SECONDS)
        return httpx.Client(base_url=self.base_url, timeout=timeout, transport=self._transport)

    @staticmethod
    def _payload(messages: Sequence[ChatMessage], options: GenerationOptions) -> dict[str, Any]:
        model_options: dict[str, Any] = {}
        if options.temperature is not None:
            model_options["temperature"] = options.temperature
        if options.max_output_tokens is not None:
            model_options["num_predict"] = options.max_output_tokens
        if options.context_window is not None:
            model_options["num_ctx"] = options.context_window
        payload: dict[str, Any] = {
            "model": options.model,
            "messages": [m.to_dict() for m in messages],
            "stream": True,
        }
        if model_options:
            payload["options"] = model_options
        return payload

    def stream(self, messages: Sequence[ChatMessage], options: GenerationOptions) -> Iterator[StreamEvent]:
        started = time.monotonic()
        parts: list[str] = []
        try:
            with self._client(options.timeout_seconds) as client:
                with client.stream("POST", "/api/chat", json=self._payload(messages, options)) as response:
                    if response.status_code != 200:
                        response.read()
                        raise self._http_error(response, options.model)
                    for line in response.iter_lines():
                        if not line.strip():
                            continue
                        data = self._parse_line(line)
                        if "error" in data:
                            raise ProviderResponseError(f"O Ollama informou um erro: {data['error']}")
                        piece = (data.get("message") or {}).get("content") or ""
                        if piece:
                            parts.append(piece)
                            yield TextDelta(piece)
                        if data.get("done"):
                            yield StreamCompleted(
                                CompletionResult(
                                    text="".join(parts),
                                    provider=self.name,
                                    model=data.get("model") or options.model,
                                    tokens_in=data.get("prompt_eval_count"),
                                    tokens_out=data.get("eval_count"),
                                    duration_ms=int((time.monotonic() - started) * 1000),
                                )
                            )
                            return
        except ProviderError:
            raise
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(
                f"Não foi possível conectar ao Ollama em {self.base_url}. Ele está instalado e aberto?"
            ) from exc
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                f"O Ollama demorou mais de {options.timeout_seconds:.0f} s para responder."
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderResponseError(f"Falha de comunicação com o Ollama: {exc}") from exc
        raise ProviderResponseError("A resposta do Ollama foi interrompida antes do fim.")

    def list_models(self) -> list[str]:
        try:
            with self._client(CONNECT_TIMEOUT_SECONDS * 2) as client:
                response = client.get("/api/tags")
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(
                f"Não foi possível conectar ao Ollama em {self.base_url}. Ele está instalado e aberto?"
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderResponseError(f"Falha de comunicação com o Ollama: {exc}") from exc
        if response.status_code != 200:
            raise self._http_error(response, None)
        try:
            return [model["name"] for model in response.json().get("models", [])]
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise ProviderResponseError("O Ollama devolveu uma lista de modelos inválida.") from exc

    @staticmethod
    def _parse_line(line: str) -> dict[str, Any]:
        try:
            data = json.loads(line)
        except ValueError as exc:
            raise ProviderResponseError("O Ollama devolveu uma resposta que não é JSON.") from exc
        if not isinstance(data, dict):
            raise ProviderResponseError("O Ollama devolveu uma resposta em formato inesperado.")
        return data

    @staticmethod
    def _http_error(response: httpx.Response, model: str | None) -> ProviderError:
        try:
            detail = response.json().get("error", "")
        except ValueError:
            detail = response.text[:300]
        if response.status_code == 404 and model:
            return ModelNotFoundError(
                f"O modelo '{model}' não está instalado no Ollama. Instale com: ollama pull {model}"
            )
        return ProviderResponseError(f"O Ollama respondeu com erro HTTP {response.status_code}: {detail}")
