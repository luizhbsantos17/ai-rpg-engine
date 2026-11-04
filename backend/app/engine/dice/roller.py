"""Rolagem reproduzível: mesma expressão + mesma semente = mesmo resultado."""

from __future__ import annotations

import hashlib
import random
import secrets
from dataclasses import dataclass, field

from app.engine.dice.notation import ConstantTerm, DiceTerm, parse_dice

SEED_BITS = 63  # cabe num inteiro de 64 bits com sinal no banco


@dataclass(frozen=True)
class TermResult:
    notation: str
    rolls: list[int] = field(default_factory=list)  # todos os dados rolados
    kept: list[int] = field(default_factory=list)  # os que contaram
    subtotal: int = 0


@dataclass(frozen=True)
class DiceRoll:
    expression: str
    seed: int
    terms: list[TermResult]
    total: int

    def to_dict(self) -> dict:
        return {
            "expression": self.expression,
            "seed": self.seed,
            "total": self.total,
            "terms": [
                {"notation": t.notation, "rolls": t.rolls, "kept": t.kept, "subtotal": t.subtotal}
                for t in self.terms
            ],
        }


def new_seed() -> int:
    """Semente nova e imprevisível (quando não há semente derivada)."""
    return secrets.randbits(SEED_BITS)


def derive_seed(base_seed: int, *parts: object) -> int:
    """Semente determinística a partir da semente da campanha e de um identificador.

    Ex.: derive_seed(campanha.rng_seed, turn_id, 0) — reproduz a mesma rolagem sempre.
    """
    material = ":".join([str(base_seed), *map(str, parts)]).encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big") >> (64 - SEED_BITS)


def roll(expression: str, seed: int) -> DiceRoll:
    terms = parse_dice(expression)
    rng = random.Random(seed)
    results: list[TermResult] = []
    total = 0
    for term in terms:
        result = _roll_term(term, rng)
        results.append(result)
        total += result.subtotal
    return DiceRoll(expression=expression, seed=seed, terms=results, total=total)


def roll_uniform(seed: int, low: int, high: int) -> int:
    """Número inteiro sorteado entre low e high (inclusive), reproduzível pela semente."""
    if low > high:
        raise ValueError("low precisa ser menor ou igual a high.")
    return random.Random(seed).randint(low, high)


def _roll_term(term, rng: random.Random) -> TermResult:
    sign_text = "-" if term.sign < 0 else "+"
    if isinstance(term, ConstantTerm):
        return TermResult(notation=f"{sign_text}{term.value}", subtotal=term.sign * term.value)

    assert isinstance(term, DiceTerm)
    rolls = [rng.randint(1, term.faces) for _ in range(term.count)]
    if term.keep == "kh":
        kept = sorted(rolls, reverse=True)[: term.keep_count]
    elif term.keep == "kl":
        kept = sorted(rolls)[: term.keep_count]
    else:
        kept = list(rolls)
    keep_text = f"{term.keep}{term.keep_count}" if term.keep else ""
    return TermResult(
        notation=f"{sign_text}{term.count}d{term.faces}{keep_text}",
        rolls=rolls,
        kept=kept,
        subtotal=term.sign * sum(kept),
    )
