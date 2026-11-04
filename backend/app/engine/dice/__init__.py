"""Dados e aleatoriedade (D-005). ÚNICO lugar do programa que pode gerar números aleatórios.

Toda rolagem usa uma semente (seed) registrada: com a mesma expressão e a mesma semente,
o resultado é sempre o mesmo. Isso permite auditar e reproduzir qualquer teste (SPEC 7.2).
"""

from app.engine.dice.notation import DiceSyntaxError, parse_dice
from app.engine.dice.roller import DiceRoll, derive_seed, new_seed, roll, roll_uniform

__all__ = ["DiceRoll", "DiceSyntaxError", "derive_seed", "new_seed", "parse_dice", "roll", "roll_uniform"]
