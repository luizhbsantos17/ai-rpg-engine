"""Contexto da narração na Etapa 1: instruções + campanha + histórico recente + ação atual.

O banco guarda tudo; a IA recebe só o que cabe no orçamento (SPEC 17.6). Nas próximas
etapas entram estado atual, resumos, memórias e registro canônico (ARCHITECTURE §7).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.ai.prompts.narrator import CampaignBrief, build_narrator_system_prompt
from app.providers import ChatMessage

# Estimativa grosseira: em português, ~4 caracteres por token. É só para o orçamento,
# não para custos (custos usam a contagem informada pelo provedor).
CHARS_PER_TOKEN_ESTIMATE = 4
# Folga para a diferença entre a estimativa e a contagem real do modelo.
SAFETY_MARGIN_TOKENS = 256


@dataclass(frozen=True)
class HistoryItem:
    role: str  # "player" ou "narration" (ou "system": avisos do jogo)
    content: str


def estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN_ESTIMATE + 1


def _to_chat_message(item: HistoryItem) -> ChatMessage:
    if item.role == "player":
        return ChatMessage("user", item.content)
    if item.role == "narration":
        return ChatMessage("assistant", item.content)
    return ChatMessage("user", f"[Aviso do jogo] {item.content}")


def build_narration_context(
    brief: CampaignBrief,
    history: Sequence[HistoryItem],
    player_input: str,
    context_window: int,
    max_output_tokens: int,
) -> list[ChatMessage]:
    """Monta as mensagens, mantendo o histórico mais recente que couber no orçamento."""
    system = ChatMessage("system", build_narrator_system_prompt(brief))
    current = ChatMessage("user", player_input)

    budget = context_window - max_output_tokens - SAFETY_MARGIN_TOKENS
    budget -= estimate_tokens(system.content) + estimate_tokens(current.content)

    kept: list[ChatMessage] = []
    for item in reversed(history):
        cost = estimate_tokens(item.content)
        if cost > budget:
            break
        kept.append(_to_chat_message(item))
        budget -= cost
    kept.reverse()

    # Alguns modelos exigem que a conversa comece pelo usuário (após o system).
    while kept and kept[0].role == "assistant":
        kept.pop(0)
    return [system, *kept, current]
