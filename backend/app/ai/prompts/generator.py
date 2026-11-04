"""Instruções do papel "gerador de campanhas" (SPEC Parte 3).

Ingredientes de inspiração são SUGESTÕES sorteadas pelo motor (dados com semente): servem
para quebrar a repetição de modelos pequenos. A IA pode combiná-los, transformá-los ou
ignorá-los e inventar algo totalmente novo (SPEC 3.1: não se limitar a listas).
"""

from __future__ import annotations

from collections.abc import Sequence

from app.engine.dice import derive_seed, roll_uniform
from app.providers import ChatMessage

INGREDIENTS = {
    "época": ["era de pedra e magia selvagem", "medieval tardio", "renascimento alquímico", "era industrial a vapor",
              "presente", "futuro próximo", "futuro distante", "depois do fim do mundo", "tempo que corre em ciclos",
              "um mundo sem noção de tempo"],
    "situação do protagonista": ["reencarnou em outro mundo", "foi invocado com toda a turma", "começa absurdamente forte",
                                 "começa fraco e desprezado", "foi traído pelos companheiros",
                                 "recebeu um poder aparentemente inútil", "despertou algo que não entende",
                                 "nasceu numa família nobre decadente", "nasceu na miséria",
                                 "é uma criatura incomum", "não tem acesso ao sistema que todos usam",
                                 "pode quebrar as regras do próprio mundo", "precisa só sobreviver"],
    "tom": ["sombrio", "esperançoso", "melancólico", "irônico", "épico", "intimista", "paranoico", "contemplativo",
            "cômico com momentos trágicos", "brutal"],
    "conflito": ["guerra entre reinos", "praga misteriosa", "deuses ausentes", "revolução", "dívida impagável",
                 "segredo de família", "invasão de outro mundo", "conspiração na corte", "fome e escassez",
                 "um crime sem solução", "a magia está morrendo", "uma profecia mentirosa"],
    "elemento estranho": ["a lua tem duas faces que brigam", "as sombras têm vontade própria",
                          "nomes verdadeiros dão poder", "memórias são moeda", "os mortos votam",
                          "o clima obedece às emoções", "toda mentira deixa marcas na pele",
                          "existe uma janela de status que só alguns veem", "cidades se movem à noite",
                          "a música é uma forma de magia"],
}

GENERATOR_RULES = """\
Você cria o início de campanhas de RPG originais e surpreendentes. Responda SOMENTE com um JSON:
{
  "title": "título curto e marcante",
  "genre_tags": ["gênero ou tema", "..."],
  "premise": "3 a 5 frases para o JOGADOR: quem ele é, onde está, o que está em jogo. Sem revelar segredos.",
  "secrets": ["segredo do mestre que o jogador não sabe", "reviravolta futura", "..."]
}
Regras:
- Seja original: combine gêneros, crie conceitos novos. Os ingredientes sugeridos são só inspiração.
- A premissa fala com o jogador ("Você...") e termina num ponto em que ele queira agir.
- "secrets": 2 a 4 segredos que dão profundidade (traições, verdades escondidas, ameaças).
  Eles NÃO aparecem na premissa.
- Respeite as preferências do jogador, se houver. Escreva em português do Brasil.
"""


def pick_ingredients(seed: int) -> dict[str, str]:
    """Um ingrediente por categoria, sorteado pelo motor com semente registrável."""
    return {
        category: options[roll_uniform(derive_seed(seed, category), 0, len(options) - 1)]
        for category, options in INGREDIENTS.items()
    }


def build_generator_messages(
    ingredients: dict[str, str],
    genres: Sequence[str] = (),
    themes: str = "",
    kept: dict[str, object] | None = None,
) -> list[ChatMessage]:
    lines = ["Ingredientes sugeridos (use, transforme ou ignore):"]
    lines += [f"- {k}: {v}" for k, v in ingredients.items()]
    if genres:
        lines.append(f"Gêneros desejados pelo jogador: {', '.join(genres)}")
    if themes:
        lines.append(f"Preferências do jogador: {themes}")
    if kept:
        lines.append("MANTENHA exatamente estes elementos (o jogador gostou deles) e crie o resto em harmonia:")
        lines += [f"- {k}: {v}" for k, v in kept.items()]
    lines.append("Responda só com o JSON.")
    return [ChatMessage("system", GENERATOR_RULES), ChatMessage("user", "\n".join(lines))]
