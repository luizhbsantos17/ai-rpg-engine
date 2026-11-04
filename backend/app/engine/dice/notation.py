"""Leitura da notação de dados.

Formato aceito (maiúsculas ou minúsculas; espaços só ao redor de + e -):
- `NdM`      N dados de M faces (N omitido = 1): `1d20`, `d6`, `3d8`
- `NdMkhK`   rola N e mantém os K maiores (vantagem): `2d20kh1`, `4d6kh3`
- `NdMklK`   rola N e mantém os K menores (desvantagem): `2d20kl1`
- números e somas/subtrações entre termos: `2d6+3`, `1d20-1+1d4`
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MAX_DICE_PER_TERM = 1000
MAX_FACES = 1_000_000
MAX_TERMS = 20
MAX_EXPRESSION_LENGTH = 200

_TERM = re.compile(r"([+-])?(?:(\d*)d(\d+)(?:(kh|kl)(\d+))?|(\d+))")


class DiceSyntaxError(ValueError):
    """Expressão de dados inválida."""


@dataclass(frozen=True)
class DiceTerm:
    sign: int  # +1 ou -1
    count: int
    faces: int
    keep: str | None = None  # "kh" | "kl" | None
    keep_count: int | None = None


@dataclass(frozen=True)
class ConstantTerm:
    sign: int
    value: int


Term = DiceTerm | ConstantTerm


def parse_dice(expression: str) -> list[Term]:
    text = re.sub(r"\s*([+-])\s*", r"\1", (expression or "").strip()).lower()
    if any(ch.isspace() for ch in text):
        # Sem isso, "2d6 3" viraria "2d63" (um dado de 63 faces).
        raise DiceSyntaxError(f"Espaço inesperado em '{expression}'. Use + ou - entre os termos.")
    if not text:
        raise DiceSyntaxError("Expressão de dados vazia.")
    if len(text) > MAX_EXPRESSION_LENGTH:
        raise DiceSyntaxError("Expressão de dados longa demais.")

    terms: list[Term] = []
    position = 0
    while position < len(text):
        match = _TERM.match(text, position)
        if not match or match.end() == position:
            raise DiceSyntaxError(f"Não entendi '{expression}' a partir de '{text[position:]}'.")
        if match.group(1) is None and terms:
            raise DiceSyntaxError(f"Falta '+' ou '-' entre os termos em '{expression}'.")
        terms.append(_build_term(match, expression))
        position = match.end()
        if len(terms) > MAX_TERMS:
            raise DiceSyntaxError(f"No máximo {MAX_TERMS} termos por expressão.")
    return terms


def _build_term(match: re.Match, expression: str) -> Term:
    sign = -1 if match.group(1) == "-" else 1
    if match.group(6) is not None:
        return ConstantTerm(sign, int(match.group(6)))

    count = int(match.group(2)) if match.group(2) else 1
    faces = int(match.group(3))
    if not 1 <= count <= MAX_DICE_PER_TERM:
        raise DiceSyntaxError(f"Quantidade de dados deve ser de 1 a {MAX_DICE_PER_TERM} em '{expression}'.")
    if not 1 <= faces <= MAX_FACES:
        raise DiceSyntaxError(f"Número de faces deve ser de 1 a {MAX_FACES} em '{expression}'.")

    keep, keep_count = match.group(4), None
    if keep:
        keep_count = int(match.group(5))
        if not 1 <= keep_count <= count:
            raise DiceSyntaxError(f"Não dá para manter {keep_count} de {count} dados em '{expression}'.")
    return DiceTerm(sign, count, faces, keep, keep_count)
