"""Avaliador de fórmulas sem `eval`.

A fórmula é lida como uma árvore (módulo `ast` do Python, só a leitura) e cada parte é
conferida contra uma lista do que é permitido. Nada é executado como código.

Permitido:
- números (calculados com Decimal: sem teto artificial e sem erros de arredondamento de float)
- textos entre aspas (ex.: comparar uma faixa nominal: `rank == "S"`)
- variáveis, inclusive com ponto: `forca`, `alvo.defesa`
- + - * / // % **, comparações (== != < <= > >=), and, or, not
- condição: `a if condicao else b`
- funções: min, max, abs, floor, ceil, round, clamp, roll("2d6") (roll só se o motor fornecer)
"""

from __future__ import annotations

import ast
import decimal
import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal

MAX_LENGTH = 500
MAX_NODES = 300
MAX_DEPTH = 40
MAX_EXPONENT = 1000
PRECISION = 100  # igual ao motor (operations/pipeline.py)

Value = Decimal | bool | str


class ExpressionError(ValueError):
    """Fórmula inválida ou que não pode ser calculada."""


@dataclass(frozen=True)
class Analysis:
    variables: frozenset[str]
    functions: frozenset[str]


_BIN_OPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
_CMP_OPS = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)
_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, ast.IfExp, ast.Call,
    ast.Constant, ast.Name, ast.Attribute, ast.Load,
    ast.UAdd, ast.USub, ast.Not, ast.And, ast.Or, *_BIN_OPS, *_CMP_OPS,
)
FUNCTION_NAMES = frozenset({"min", "max", "abs", "floor", "ceil", "round", "clamp", "roll"})


def _context() -> decimal.Context:
    return decimal.Context(prec=PRECISION, Emax=10**6, Emin=-(10**6), traps=[
        decimal.InvalidOperation, decimal.DivisionByZero, decimal.Overflow,
    ])


def _parse(expression: str) -> ast.Expression:
    if not isinstance(expression, str) or not expression.strip():
        raise ExpressionError("Fórmula vazia.")
    if len(expression) > MAX_LENGTH:
        raise ExpressionError(f"Fórmula longa demais (máximo {MAX_LENGTH} caracteres).")
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(f"Fórmula com erro de escrita: {exc.msg}.") from None
    nodes = list(ast.walk(tree))
    if len(nodes) > MAX_NODES:
        raise ExpressionError("Fórmula complexa demais.")
    for node in nodes:
        if not isinstance(node, _ALLOWED_NODES):
            raise ExpressionError(f"Elemento não permitido em fórmulas: {type(node).__name__}.")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float, str)):
            raise ExpressionError("Só números e textos são permitidos como valores fixos.")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTION_NAMES:
                raise ExpressionError("Função não permitida em fórmulas.")
            if node.keywords:
                raise ExpressionError("Funções em fórmulas não aceitam argumentos nomeados.")
    _check_depth(tree.body, 0)
    return tree


def _check_depth(node: ast.AST, depth: int) -> None:
    if depth > MAX_DEPTH:
        raise ExpressionError("Fórmula aninhada demais.")
    for child in ast.iter_child_nodes(node):
        _check_depth(child, depth + 1)


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_dotted_name(node.value)}.{node.attr}"
    raise ExpressionError("Nome de variável inválido.")


def analyze(expression: str) -> Analysis:
    """Confere a fórmula sem calcular e diz quais variáveis e funções ela usa."""
    tree = _parse(expression)
    variables: set[str] = set()
    _collect_names(tree.body, variables)
    functions = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call)}
    return Analysis(frozenset(variables - {"true", "false", "verdadeiro", "falso"}), frozenset(functions))


def _collect_names(node: ast.AST, out: set[str]) -> None:
    if isinstance(node, (ast.Name, ast.Attribute)):
        out.add(_dotted_name(node))
        return
    if isinstance(node, ast.Call):
        for arg in node.args:
            _collect_names(arg, out)
        return
    for child in ast.iter_child_nodes(node):
        _collect_names(child, out)


def evaluate(
    expression: str,
    variables: Mapping[str, object] | None = None,
    roller: Callable[[str], int] | None = None,
) -> Value:
    """Calcula a fórmula. `roller` recebe uma notação de dados e devolve o total (do engine/dice)."""
    tree = _parse(expression)
    evaluator = _Evaluator({k: _to_value(v, k) for k, v in (variables or {}).items()}, roller)
    try:
        with decimal.localcontext(_context()):
            return evaluator.visit(tree.body)
    except decimal.DivisionByZero:
        raise ExpressionError("Divisão por zero na fórmula.") from None
    except decimal.Overflow:
        raise ExpressionError("Resultado grande demais para calcular.") from None
    except decimal.InvalidOperation:
        raise ExpressionError("Operação matemática inválida na fórmula.") from None


def _to_value(value: object, name: str) -> Value:
    if isinstance(value, bool):
        return value
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ExpressionError(f"Variável '{name}' não é um número finito.")
        return Decimal(str(value))
    if isinstance(value, str):
        return value
    raise ExpressionError(f"Variável '{name}' tem um tipo que fórmulas não aceitam.")


class _Evaluator:
    def __init__(self, variables: dict[str, Value], roller: Callable[[str], int] | None):
        self.variables = variables
        self.roller = roller

    def visit(self, node: ast.AST) -> Value:
        method = getattr(self, f"_{type(node).__name__}", None)
        if method is None:  # protegido por _parse; defesa extra
            raise ExpressionError(f"Elemento não permitido: {type(node).__name__}.")
        return method(node)

    def _number(self, node: ast.AST) -> Decimal:
        value = self.visit(node)
        if isinstance(value, bool) or not isinstance(value, Decimal):
            raise ExpressionError("Esperava um número na fórmula.")
        return value

    def _Constant(self, node: ast.Constant) -> Value:
        return _to_value(node.value, "valor fixo")

    def _Name(self, node: ast.Name) -> Value:
        return self._lookup(node.id)

    def _Attribute(self, node: ast.Attribute) -> Value:
        return self._lookup(_dotted_name(node))

    def _lookup(self, name: str) -> Value:
        if name in ("true", "verdadeiro"):
            return True
        if name in ("false", "falso"):
            return False
        if name not in self.variables:
            raise ExpressionError(f"Variável desconhecida na fórmula: '{name}'.")
        return self.variables[name]

    def _UnaryOp(self, node: ast.UnaryOp) -> Value:
        if isinstance(node.op, ast.Not):
            return not self._truth(node.operand)
        value = self._number(node.operand)
        return -value if isinstance(node.op, ast.USub) else +value

    def _BinOp(self, node: ast.BinOp) -> Decimal:
        left, right = self._number(node.left), self._number(node.right)
        op = node.op
        if isinstance(op, ast.Add):
            return left + right
        if isinstance(op, ast.Sub):
            return left - right
        if isinstance(op, ast.Mult):
            return left * right
        if isinstance(op, ast.Div):
            return left / right
        if isinstance(op, ast.FloorDiv):
            return (left / right).to_integral_value(rounding=decimal.ROUND_FLOOR)
        if isinstance(op, ast.Mod):
            return left - right * (left / right).to_integral_value(rounding=decimal.ROUND_FLOOR)
        if abs(right) > MAX_EXPONENT:
            raise ExpressionError(f"Expoente maior que {MAX_EXPONENT} não é permitido.")
        return left**right

    def _truth(self, node: ast.AST) -> bool:
        value = self.visit(node)
        if isinstance(value, bool):
            return value
        if isinstance(value, Decimal):
            return value != 0
        return value != ""

    def _BoolOp(self, node: ast.BoolOp) -> bool:
        if isinstance(node.op, ast.And):
            return all(self._truth(v) for v in node.values)
        return any(self._truth(v) for v in node.values)

    def _Compare(self, node: ast.Compare) -> bool:
        left = self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            if not self._compare(op, left, right):
                return False
            left = right
        return True

    @staticmethod
    def _compare(op: ast.cmpop, left: Value, right: Value) -> bool:
        if isinstance(op, ast.Eq):
            return left == right
        if isinstance(op, ast.NotEq):
            return left != right
        if type(left) is not type(right) or isinstance(left, bool):
            raise ExpressionError("Só dá para comparar números com números (ou textos com textos).")
        if isinstance(op, ast.Lt):
            return left < right
        if isinstance(op, ast.LtE):
            return left <= right
        if isinstance(op, ast.Gt):
            return left > right
        return left >= right

    def _IfExp(self, node: ast.IfExp) -> Value:
        return self.visit(node.body) if self._truth(node.test) else self.visit(node.orelse)

    def _Call(self, node: ast.Call) -> Value:
        name = node.func.id
        if name == "roll":
            return self._roll(node)
        args = [self._number(a) for a in node.args]
        if name in ("min", "max"):
            if not args:
                raise ExpressionError(f"{name}() precisa de pelo menos um número.")
            return min(args) if name == "min" else max(args)
        if name == "clamp":
            if len(args) != 3:
                raise ExpressionError("clamp(valor, mínimo, máximo) precisa de 3 números.")
            value, low, high = args
            return max(low, min(high, value))
        if len(args) not in (1, 2) or (name != "round" and len(args) != 1):
            raise ExpressionError(f"{name}() recebeu a quantidade errada de números.")
        value = args[0]
        if name == "abs":
            return abs(value)
        if name == "floor":
            return value.to_integral_value(rounding=decimal.ROUND_FLOOR)
        if name == "ceil":
            return value.to_integral_value(rounding=decimal.ROUND_CEILING)
        places = int(args[1]) if len(args) == 2 else 0
        if not 0 <= places <= 20:
            raise ExpressionError("round() aceita de 0 a 20 casas decimais.")
        return value.quantize(Decimal(1).scaleb(-places), rounding=decimal.ROUND_HALF_UP)

    def _roll(self, node: ast.Call) -> Decimal:
        if self.roller is None:
            raise ExpressionError("Esta fórmula rola dados, mas nenhum rolador do motor foi fornecido.")
        if len(node.args) != 1:
            raise ExpressionError('roll() recebe uma notação de dados, ex.: roll("2d6").')
        notation = self.visit(node.args[0])
        if not isinstance(notation, str):
            raise ExpressionError('roll() recebe a notação entre aspas, ex.: roll("2d6").')
        return Decimal(self.roller(notation))
