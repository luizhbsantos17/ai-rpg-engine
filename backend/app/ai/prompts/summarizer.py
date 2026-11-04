"""Instruções do papel "resumidor": condensa trechos da campanha para a memória narrativa."""

from __future__ import annotations

from collections.abc import Sequence

from app.providers import ChatMessage

SUMMARIZER_RULES = """\
Você resume trechos de uma campanha de RPG para servirem de memória. Escreva em português do Brasil,
em terceira pessoa, em no máximo 150 palavras, num único parágrafo.
Guarde o que importa para o futuro: nomes, lugares, decisões do protagonista, promessas, dívidas,
inimigos e aliados, mistérios em aberto, ferimentos e consequências. Só fatos que aconteceram;
não invente nada e não comente o estilo. Responda só com o resumo."""


def build_summarizer_messages(campaign_title: str, turns: Sequence[tuple[int, str, str]]) -> list[ChatMessage]:
    """`turns`: (número do turno, ação do jogador, narração)."""
    body = "\n\n".join(f"[Turno {n}] Jogador: {action}\nNarração: {narration}" for n, action, narration in turns)
    return [ChatMessage("system", SUMMARIZER_RULES),
            ChatMessage("user", f"Campanha: {campaign_title}\n\n{body}\n\nResuma.")]
