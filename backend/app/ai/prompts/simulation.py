"""Instruções do papel "simulação do mundo": o que aconteceu longe do protagonista (SPEC 8.1, 8.4, 10.2)."""

from __future__ import annotations

from collections.abc import Sequence

from app.ai.prompts.narrator import CampaignBrief, memory_lines
from app.providers import ChatMessage

SIMULATION_RULES = """\
Você simula o mundo de um RPG enquanto o tempo passa LONGE do protagonista. Você NÃO narra para o jogador.
Responda SOMENTE com um JSON: {"summary": "o que aconteceu, em 1 a 3 frases", "operations": [ ... ]}.

Use as mesmas operações do motor (entity.update, entity.move, attribute.modify, relationship.change,
memory.record, knowledge.record, canon.assert, quest.update, event.schedule, item.transfer, event.record...).
Não use time.advance (o tempo já passou).

Regras:
- Cada personagem listado age conforme a SUA personalidade, objetivos e o que ele sabe. Nada aleatório sem sentido.
- Pode haver 0 a 2 acontecimentos do mundo (guerra, desastre, descoberta, mudança política...) coerentes com os
  fatos. Registre-os com canon.assert (status "rumor" se só se fala disso) ou event.record.
- Mudanças proporcionais ao tempo que passou. Se nada importante aconteceu, "operations": [].
- Não mexa no protagonista: ele não estava lá.
- Referências: use os apelidos da lista (n1, n2...) ou ids.
"""


def build_simulation_messages(brief: CampaignBrief, elapsed_text: str, now_text: str,
                              npc_lines: Sequence[str]) -> list[ChatMessage]:
    lines = [SIMULATION_RULES, "", "Campanha:", f"- Título: {brief.title}"]
    if brief.gm_secret:
        lines.append("- Segredos do mestre: " + "; ".join(f"{k}: {v}" for k, v in brief.gm_secret.items()))
    if brief.canon:
        lines.append("- Fatos do mundo: " + " | ".join(statement for _, statement in brief.canon))
    lines.extend(memory_lines(brief))
    npcs = "\n".join(npc_lines) if npc_lines else "(nenhum personagem relevante longe da cena)"
    user = (f"Passaram-se {elapsed_text}; agora é {now_text}.\n\nPERSONAGENS RELEVANTES LONGE DO PROTAGONISTA:\n{npcs}"
            "\n\nResponda só com o JSON.")
    return [ChatMessage("system", "\n".join(lines)), ChatMessage("user", user)]
