"""Serviços de IA na internet com uso GRATUITO, prontos para usar (D-054).

Todos falam o formato da OpenAI; cada atalho só preenche endereço, chave, modelo preferido e as
travas para nunca cair num modelo pago. Limites e regras mudam: conferidos em 2026-11-04 (ver
docs/AI_PROVIDERS.md, com as fontes). O dono cria a conta e a chave; nada aqui cobra.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# Nomes de modelos que não servem para conversa (imagem, voz, vetores...).
NOT_CHAT = ("embedding", "image", "tts", "audio", "live", "whisper", "guard", "safety", "orpheus", "veo", "imagen")


@dataclass(frozen=True)
class FreeService:
    name: str  # valor de AI_PROVIDER
    label: str
    base_url: str
    key_env: str  # variável do .env com a chave
    key_url: str  # onde o dono cria a chave
    preferred_models: tuple[str, ...]  # em ordem; o primeiro que existir no serviço é usado
    content_note: str
    allows_model: Callable[[str], bool] = lambda model: True  # trava: modelos que podem ser usados
    extra_payload: Callable[[str], dict[str, Any]] = lambda model: {}
    headers: dict[str, str] = field(default_factory=dict)

    def pick_model(self, available: list[str]) -> str | None:
        usable = [m for m in available if self.allows_model(m) and not any(w in m.lower() for w in NOT_CHAT)]
        for wanted in self.preferred_models:
            for model in usable:
                if model == wanted or model.endswith("/" + wanted):
                    return model
        return usable[0] if usable else None


def _groq_extra(model: str) -> dict[str, Any]:
    # gpt-oss "pensa" antes de responder e esse pensamento gasta o limite de tokens da resposta.
    return {"reasoning_effort": "low"} if model.startswith("openai/gpt-oss") else {}


FREE_SERVICES: dict[str, FreeService] = {
    "gemini": FreeService(
        name="gemini", label="Google Gemini (AI Studio)",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        key_env="GEMINI_API_KEY", key_url="https://aistudio.google.com/apikey",
        preferred_models=("gemini-3.8-flash", "gemini-2.5-flash", "gemini-flash-latest"),
        content_note=("O Gemini tem filtros de segurança próprios: pode recusar conteúdo sexual explícito ou "
                      "violência extrema, mesmo que a campanha permita."),
    ),
    "groq": FreeService(
        name="groq", label="Groq",
        base_url="https://api.groq.com/openai/v1",
        key_env="GROQ_API_KEY", key_url="https://console.groq.com/keys",
        preferred_models=("openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"),
        content_note="Os modelos do Groq seguem regras de uso próprias e podem recusar conteúdo explícito.",
        extra_payload=_groq_extra,
    ),
    "openrouter": FreeService(
        name="openrouter", label="OpenRouter (só modelos gratuitos)",
        base_url="https://openrouter.ai/api/v1",
        key_env="OPENROUTER_API_KEY", key_url="https://openrouter.ai/keys",
        preferred_models=("google/gemma-4-31b-it:free", "google/gemma-4-26b-a4b-it:free"),
        content_note="Na OpenRouter, o que é aceito depende do modelo gratuito escolhido e de quem o hospeda.",
        # Trava: só modelos ":free". Um modelo pago cobraria se a conta tivesse créditos.
        allows_model=lambda model: model.endswith(":free"),
        headers={"X-Title": "AI RPG Engine"},
    ),
}
