"""Adaptador para servidores no formato da API da OpenAI (D-053).

Muitos programas e serviços usam esse formato: LM Studio, llama.cpp, vLLM e o próprio Ollama (em /v1),
além de serviços pagos. API usada: POST {base}/chat/completions com "stream": true (eventos SSE
"data: {...}" terminando em "data: [DONE]") e GET {base}/models.

Serviços pagos ficam bloqueados na configuração até existir controle de gasto (ver config.py).
Serviços gratuitos prontos (Gemini, Groq, OpenRouter) usam este adaptador com um `FreeService`.

Robustez para serviços na internet:
- limite de pedidos (HTTP 429): espera o tempo pedido pelo serviço e tenta de novo, antes de qualquer texto;
- modelo que não aceita o esquema JSON completo: tenta "json_object" e, se preciso, só as instruções do prompt;
- serviço gratuito com o modelo sobrecarregado ou sem cota: tenta o próximo modelo recomendado (só com
  escolha automática, AI_MODEL vazio) e passa a usar o que respondeu.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator, Sequence
from contextlib import closing
from dataclasses import replace
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
from app.providers.free_services import FreeService
from app.providers.errors import (
    ModelNotFoundError,
    ProviderError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT_SECONDS = 10.0
DONE = "[DONE]"
RATE_LIMIT_RETRIES = 3
RETRYABLE_STATUS = (502, 503, 504)  # serviço sobrecarregado ou fora do ar por um momento: esperar e tentar de novo
RATE_LIMIT_MAX_WAIT_SECONDS = 60.0
MODELS_CACHE_SECONDS = 600.0
MAX_FALLBACK_MODELS = 3  # quantos modelos tentar, no total, quando o escolhido está sobrecarregado
JSON_MODES = ("json_schema", "json_object", "none")  # do mais exigente ao mais simples


class RateLimitedError(ProviderError):
    """O serviço pediu para esperar (limite de pedidos)."""

    retryable = True


class OpenAICompatProvider(AIProvider):
    name = "openai_compat"
    content_note = ("Em servidores no formato OpenAI, o que é aceito em temas adultos depende do modelo e das "
                    "regras do serviço; serviços externos costumam recusar conteúdo explícito.")

    def __init__(self, base_url: str, api_key: str | None = None, paid: bool = True,
                 transport: httpx.BaseTransport | None = None, service: FreeService | None = None,
                 auto_fallback: bool = False):
        self.base_url = base_url.rstrip("/")
        self.is_paid = paid
        self.service = service
        if service is not None:
            self.name = service.name
            self.content_note = service.content_note
        self._api_key = api_key
        self._transport = transport  # usado pelos testes para simular o servidor
        self._sleep = time.sleep  # trocado nos testes (não esperar de verdade)
        self._json_mode: dict[str, str] = {}  # modo JSON que funcionou em cada modelo
        self._models: tuple[float, list[str]] | None = None
        self.auto_fallback = auto_fallback and service is not None  # trocar de modelo se o escolhido falhar
        self._working_model: str | None = None  # modelo que respondeu depois de uma troca

    def __repr__(self) -> str:  # nunca mostra a chave
        return f"OpenAICompatProvider(name={self.name!r}, base_url={self.base_url!r}, paid={self.is_paid})"

    def _client(self, timeout_seconds: float) -> httpx.Client:
        headers = dict(self.service.headers) if self.service else {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        timeout = httpx.Timeout(timeout_seconds, connect=CONNECT_TIMEOUT_SECONDS)
        return httpx.Client(base_url=self.base_url, timeout=timeout, headers=headers, transport=self._transport)

    def choose_model(self, models: list[str]) -> str | None:
        if self._working_model in models:
            return self._working_model
        if self.service is not None:
            return self.service.pick_model(models)
        return models[0] if models else None

    def _payload(self, messages: Sequence[ChatMessage], options: GenerationOptions, json_mode: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": options.model,
            "messages": [m.to_dict() for m in messages],
            "stream": True,
            "stream_options": {"include_usage": True},  # contagem de tokens no último evento
        }
        if options.temperature is not None:
            payload["temperature"] = options.temperature
        if options.max_output_tokens is not None:
            payload["max_tokens"] = options.max_output_tokens
        if options.json_schema is not None and json_mode == "json_schema":
            payload["response_format"] = {"type": "json_schema",
                                          "json_schema": {"name": "resposta", "schema": options.json_schema}}
        elif options.json_schema is not None and json_mode == "json_object":
            payload["response_format"] = {"type": "json_object"}
        if self.service is not None:
            payload.update(self.service.extra_payload(options.model))
        # context_window não existe neste formato: quem define é o servidor.
        return payload

    def stream(self, messages: Sequence[ChatMessage], options: GenerationOptions) -> Iterator[StreamEvent]:
        if self.service is not None and not self.service.allows_model(options.model):
            raise ProviderResponseError(
                f"O modelo '{options.model}' não é gratuito em {self.service.label}; ele foi bloqueado para não gerar cobrança.")
        candidates = self._candidates(options.model)
        for index, model in enumerate(candidates):
            last = index == len(candidates) - 1
            got_text = False
            try:
                for event in self._stream_model(messages, replace(options, model=model), patient=last):
                    got_text = got_text or isinstance(event, TextDelta)
                    if isinstance(event, StreamCompleted) and model != options.model:
                        self._working_model = model  # antes do yield: quem lê pode parar no resultado final
                    yield event
            except (RateLimitedError, ProviderUnavailableError) as exc:
                if last or got_text:
                    raise
                logger.warning("Modelo %s indisponível (%s); tentando %s", model, exc.message, candidates[index + 1])
                continue
            return

    def _candidates(self, model: str) -> list[str]:
        """O modelo pedido e, com troca automática, os próximos recomendados que existem no serviço."""
        if not self.auto_fallback:
            return [model]
        try:
            available = self.list_models()
        except ProviderError:
            return [model]
        others = [m for m in self.service.preferred_models if m in available and m != model]
        return [model, *others][:MAX_FALLBACK_MODELS]

    def _stream_model(self, messages: Sequence[ChatMessage], options: GenerationOptions,
                      patient: bool) -> Iterator[StreamEvent]:
        started = time.monotonic()
        parts: list[str] = []
        usage: dict[str, Any] = {}
        model = options.model
        finished = False
        try:
            with self._client(options.timeout_seconds) as client:
                with closing(self._open(client, messages, options, patient)) as response:
                    for line in response.iter_lines():
                        if not line.startswith("data:"):
                            continue  # linhas vazias e comentários ": ping" do SSE
                        body = line[len("data:"):].strip()
                        if body == DONE:
                            finished = True
                            break
                        data = self._parse(body)
                        if data.get("error"):
                            raise ProviderResponseError(f"O servidor de IA informou um erro: {_message(data['error'])}")
                        model = data.get("model") or model
                        usage = data.get("usage") or usage
                        for choice in data.get("choices") or []:
                            piece = (choice.get("delta") or {}).get("content") or ""
                            if piece:
                                parts.append(piece)
                                yield TextDelta(piece)
                            if choice.get("finish_reason"):
                                finished = True  # alguns servidores não mandam [DONE]; o uso pode vir depois
        except ProviderError:
            raise
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(f"Não foi possível conectar ao servidor de IA em {self.base_url}.") from exc
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                f"O servidor de IA demorou mais de {options.timeout_seconds:.0f} s para responder.") from exc
        except httpx.HTTPError as exc:
            raise ProviderResponseError(f"Falha de comunicação com o servidor de IA: {exc}") from exc
        if not finished:
            raise ProviderResponseError("A resposta do servidor de IA foi interrompida antes do fim.")
        yield StreamCompleted(CompletionResult(
            text="".join(parts), provider=self.name, model=model,
            tokens_in=usage.get("prompt_tokens"), tokens_out=usage.get("completion_tokens"),
            duration_ms=int((time.monotonic() - started) * 1000),
        ))

    def _open(self, client: httpx.Client, messages: Sequence[ChatMessage], options: GenerationOptions,
              patient: bool = True):
        """Abre o stream. Antes de chegar qualquer texto, ainda dá para esperar (429) ou simplificar o JSON.

        `patient=False` (há outro modelo para tentar): no 503 (sobrecarga) espera uma vez só; no 429 de limite
        por minuto espera do mesmo jeito (passa rápido e o modelo preferido é melhor que o reserva).
        """
        json_mode = self._json_mode.get(options.model, JSON_MODES[0])
        overload_waits = RATE_LIMIT_RETRIES if patient else 1
        waits = 0
        while True:
            response = client.send(client.build_request(
                "POST", "/chat/completions", json=self._payload(messages, options, json_mode)), stream=True)
            if response.status_code == 200:
                if options.json_schema is not None:
                    self._json_mode[options.model] = json_mode
                return response
            response.read()
            response.close()
            max_waits = RATE_LIMIT_RETRIES if response.status_code == 429 else overload_waits
            if response.status_code in (429, *RETRYABLE_STATUS) and waits < max_waits:
                wait = _retry_after(response, waits + 1)
                if wait <= RATE_LIMIT_MAX_WAIT_SECONDS:  # cota diária esgotada ("volte em 7 h"): não adianta esperar
                    waits += 1
                    self._sleep(wait)
                    continue
            simpler = _simpler_json_mode(json_mode)
            if response.status_code == 400 and options.json_schema is not None and simpler is not None:
                json_mode = simpler  # modelo sem suporte ao formato pedido: o prompt já pede JSON
                continue
            raise self._http_error(response, options.model)

    def list_models(self) -> list[str]:
        if self._models is not None and time.monotonic() - self._models[0] < MODELS_CACHE_SECONDS:
            return list(self._models[1])
        try:
            with self._client(CONNECT_TIMEOUT_SECONDS * 2) as client:
                response = client.get("/models")
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(f"Não foi possível conectar ao servidor de IA em {self.base_url}.") from exc
        except httpx.HTTPError as exc:
            raise ProviderResponseError(f"Falha de comunicação com o servidor de IA: {exc}") from exc
        if response.status_code != 200:
            raise self._http_error(response, None)
        try:
            # Gemini devolve "models/gemini-..."; no pedido de conversa o nome vai sem o prefixo.
            models = [model["id"].removeprefix("models/") for model in response.json().get("data", [])]
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise ProviderResponseError("O servidor de IA devolveu uma lista de modelos inválida.") from exc
        if self.service is not None:
            models = [m for m in models if self.service.allows_model(m)]
        self._models = (time.monotonic(), models)
        return list(models)

    @staticmethod
    def _parse(body: str) -> dict[str, Any]:
        try:
            data = json.loads(body)
        except ValueError as exc:
            raise ProviderResponseError("O servidor de IA devolveu um evento que não é JSON.") from exc
        if not isinstance(data, dict):
            raise ProviderResponseError("O servidor de IA devolveu um evento em formato inesperado.")
        return data

    def _http_error(self, response: httpx.Response, model: str | None) -> ProviderError:
        try:
            body = response.json()
        except ValueError:
            body = None
        if isinstance(body, list) and body:  # o Gemini devolve [{"error": {...}}]
            body = body[0]
        detail = _message(body.get("error", "")) if isinstance(body, dict) else response.text[:300]
        key_name = self.service.key_env if self.service else "OPENAI_COMPAT_API_KEY"
        if response.status_code in (401, 403):
            return ProviderResponseError(f"O servidor de IA recusou a chave ({key_name} inválida ou sem acesso). {detail}".strip())
        if response.status_code == 404 and model:
            return ModelNotFoundError(f"O modelo '{model}' não existe nesse servidor de IA. {detail}".strip())
        if response.status_code == 429:
            return RateLimitedError("O servidor de IA pediu para esperar (limite de pedidos). Tente de novo daqui a "
                                    f"pouco. {detail}".strip())
        if response.status_code in RETRYABLE_STATUS:
            return ProviderUnavailableError(f"O serviço de IA está sobrecarregado ou fora do ar agora (HTTP "
                                            f"{response.status_code}). Tente de novo daqui a pouco. {detail}".strip())
        return ProviderResponseError(f"O servidor de IA respondeu com erro HTTP {response.status_code}: {detail}")


def _retry_after(response: httpx.Response, attempt: int) -> float:
    """Segundos que o serviço pediu para esperar (cabeçalho Retry-After ou "retryDelay" do Gemini); sem
    indicação, 5 s, 10 s... Pode passar do máximo: aí quem chama desiste em vez de esperar."""
    try:
        return max(0.0, float(response.headers.get("retry-after", "")))
    except ValueError:
        pass
    delay = _gemini_retry_delay(response)
    return delay if delay is not None else 5.0 * attempt


def _gemini_retry_delay(response: httpx.Response) -> float | None:
    """O Gemini informa a espera no corpo: [{"error": {"details": [{"retryDelay": "26754s"}]}}]."""
    try:
        body = response.json()
    except ValueError:
        return None
    body = body[0] if isinstance(body, list) and body else body
    error = body.get("error") if isinstance(body, dict) else None
    details = error.get("details", []) if isinstance(error, dict) else []
    for detail in details if isinstance(details, list) else []:
        raw = detail.get("retryDelay") if isinstance(detail, dict) else None
        if isinstance(raw, str) and raw.endswith("s"):
            try:
                return float(raw[:-1])
            except ValueError:
                return None
    return None


def _simpler_json_mode(mode: str) -> str | None:
    index = JSON_MODES.index(mode)
    return JSON_MODES[index + 1] if index + 1 < len(JSON_MODES) else None


def _message(error: Any) -> str:
    """O campo "error" vem como texto ou como {"message": ...}, conforme o servidor."""
    if isinstance(error, dict):
        return str(error.get("message") or error)[:300]
    return str(error)[:300]
