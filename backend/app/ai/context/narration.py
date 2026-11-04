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


REJECTED_EXCERPT_CHARS = 1200  # trecho da versão recusada mostrado à IA (para ela não repetir)


def with_engine_facts(player_input: str, facts: Sequence[str], scene_notes: Sequence[str] = (),
                      rejected: str | None = None) -> str:
    """Ação do jogador + resultados reais do motor (só no turno atual; o histórico guarda só a ação)."""
    text = player_input
    if facts:
        listed = "\n".join(f"- {fact}" for fact in facts)
        text += f"\n\nRESULTADOS DO MOTOR (fatos que já aconteceram; narre de acordo):\n{listed}"
    if scene_notes:
        listed = "\n".join(f"- {note}" for note in scene_notes)
        text += ("\n\nO QUE CADA PERSONAGEM PRESENTE SABE (cada um só age e fala com base no que sabe):\n"
                 f"{listed}")
    if rejected:
        excerpt = rejected.strip()[:REJECTED_EXCERPT_CHARS]
        text += ("\n\nO JOGADOR PEDIU OUTRA VERSÃO desta narração. Escreva uma diferente: outras palavras, outros "
                 "detalhes e outro jeito de conduzir a cena, com os MESMOS resultados do motor. Versão recusada "
                 f"(não repita):\n«{excerpt}»")
    return text


def build_narration_context(
    brief: CampaignBrief,
    history: Sequence[HistoryItem],
    player_input: str,
    context_window: int,
    max_output_tokens: int,
    mechanics: bool = False,
    facts: Sequence[str] = (),
    scene_notes: Sequence[str] = (),
    rejected: str | None = None,
) -> list[ChatMessage]:
    """Monta as mensagens, mantendo o histórico mais recente que couber no orçamento."""
    system = ChatMessage("system", build_narrator_system_prompt(brief, mechanics))
    current = ChatMessage("user", with_engine_facts(player_input, facts, scene_notes, rejected))

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
