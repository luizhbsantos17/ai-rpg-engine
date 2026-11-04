from decimal import Decimal

import pytest

from app.engine.dice import roll
from app.engine.expressions import ExpressionError, analyze, evaluate


@pytest.mark.parametrize(
    "formula,variables,expected",
    [
        ("forca * 1.5 + nivel", {"forca": 10, "nivel": 3}, Decimal("18.0")),
        ("0.1 + 0.2", {}, Decimal("0.3")),  # Decimal: sem o erro clássico do float
        ("7 // 2", {}, Decimal(3)),
        ("-7 // 2", {}, Decimal(-4)),
        ("7 % 3", {}, Decimal(1)),
        ("2 ** 10", {}, Decimal(1024)),
        ("min(5, 2, 9) + max(1, 4)", {}, Decimal(6)),
        ("clamp(150, 0, 100)", {}, Decimal(100)),
        ("floor(2.7) + ceil(2.1) + abs(-3)", {}, Decimal(8)),
        ("round(2.345, 2)", {}, Decimal("2.35")),
        ("alvo.defesa - 2", {"alvo.defesa": 12}, Decimal(10)),
        ("10 if mana >= custo else 0", {"mana": 5, "custo": 8}, Decimal(0)),
    ],
)
def test_arithmetic(formula, variables, expected):
    assert evaluate(formula, variables) == expected


def test_comparisons_and_logic():
    assert evaluate("nivel > 3 and not amaldicoado", {"nivel": 5, "amaldicoado": False}) is True
    assert evaluate("1 < x <= 10", {"x": 10}) is True
    assert evaluate('rank == "S"', {"rank": "S"}) is True
    assert evaluate("ativo or false", {"ativo": False}) is False


def test_no_artificial_ceiling_for_big_numbers():
    value = evaluate("poder * 10 ** 300", {"poder": Decimal("9.99e500")})
    assert value > Decimal("1e800")


def test_roll_uses_engine_roller():
    result = evaluate('roll("2d6") + forca', {"forca": 3}, roller=lambda n: roll(n, seed=42).total)
    assert result == roll("2d6", seed=42).total + 3


def test_roll_without_roller_is_refused():
    with pytest.raises(ExpressionError, match="rolador"):
        evaluate('roll("1d20")')


@pytest.mark.parametrize(
    "formula",
    [
        "__import__('os').system('echo hack')",
        "().__class__.__bases__[0].__subclasses__()",
        "open('arquivo.txt')",
        "forca.__class__",
        "[x for x in range(10)]",
        "lambda: 1",
        "(x := 5)",
        "forca[0]",
        "{'a': 1}",
        "f'{forca}'",
        "max(1, key=abs)",
        "eval('1+1')",
    ],
)
def test_malicious_or_unsupported_formulas_are_refused(formula):
    with pytest.raises(ExpressionError):
        evaluate(formula, {"forca": 1})


@pytest.mark.parametrize(
    "formula,variables,message",
    [
        ("1 / 0", {}, "zero"),
        ("x + 1", {}, "desconhecida"),
        ("2 ** 100000", {}, "Expoente"),
        ("(10 ** 1000) ** 1000 * 10 ** 1000", {}, "grande demais"),
        ('"texto" + 1', {}, "número"),
        ('nome < 3', {"nome": "Ana"}, "comparar"),
        ("1 +", {}, "erro de escrita"),
        ("", {}, "vazia"),
        ("1+" * 400 + "1", {}, "longa"),
        ("(-8) ** 0.5", {}, "inválida"),
    ],
)
def test_calculation_errors_are_clear(formula, variables, message):
    with pytest.raises(ExpressionError, match=message):
        evaluate(formula, variables)


def test_deep_nesting_is_refused():
    with pytest.raises(ExpressionError, match="aninhada"):
        evaluate("abs(" * 45 + "1" + ")" * 45)


def test_redundant_parentheses_are_fine():
    # Parênteses não criam aninhamento real na árvore da fórmula.
    assert evaluate("(" * 60 + "1" + ")" * 60) == Decimal(1)


def test_non_finite_variables_are_refused():
    with pytest.raises(ExpressionError, match="finito"):
        evaluate("x + 1", {"x": float("inf")})


def test_analyze_lists_variables_without_calculating():
    result = analyze('forca * 2 + alvo.defesa + roll("1d6") if ativo else 0')
    assert result.variables == {"forca", "alvo.defesa", "ativo"}
    assert result.functions == {"roll"}
