"""check.request — o motor rola os dados; a IA só define o que está em jogo (D-005).

Resultado = dados + modificador, comparado com a dificuldade. Modificador e dificuldade
podem ser fórmulas com atributos do ator e do alvo (ex.: "forca - target.defesa").
Toda rolagem fica em `dice_rolls` com a semente, para auditoria e reprodução.
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.dice import DiceSyntaxError, roll
from app.engine.errors import OperationRejected
from app.engine.expressions import ExpressionError, evaluate
from app.engine.operations.context import OperationContext
from app.engine.operations.schemas import CheckRequest
from app.engine.rules.values import number_text, to_decimal
from app.engine.rules.variables import check_variables


def check_request(op: CheckRequest, ctx: OperationContext) -> dict:
    actor = ctx.entity(op.actor, allow_dead=False)
    target = ctx.entity(op.target) if op.target else None
    variables = check_variables(ctx.data, actor, target)
    roller = _roller(ctx, op.label, actor.id)

    modifier = _value(op.modifier, variables, roller, "modificador")
    difficulty = _value(op.difficulty, variables, roller, "dificuldade")
    try:
        dice = roll(op.dice, ctx.next_seed())
    except DiceSyntaxError as exc:
        raise OperationRejected(f"Dados inválidos: {exc}") from None

    natural = sum(sum(t.kept) for t in dice.terms if t.rolls)
    total = Decimal(dice.total) + modifier
    critical_success = op.critical_success is not None and natural >= to_decimal(op.critical_success)
    critical_failure = op.critical_failure is not None and natural <= to_decimal(op.critical_failure)
    success = (total >= difficulty or critical_success) and not critical_failure

    result = {
        "label": op.label,
        "actor_id": actor.id, "actor": actor.name,
        "target_id": target.id if target else None, "target": target.name if target else None,
        "dice": dice.to_dict(), "natural": natural,
        "modifier": number_text(modifier), "difficulty": number_text(difficulty), "total": number_text(total),
        "margin": number_text(total - difficulty),
        "success": success, "critical_success": critical_success, "critical_failure": critical_failure,
    }
    ctx.data.dice_rolls.record(op.dice, dice.seed, dice.total, {"check": result}, ctx.turn_id)
    if op.ref:
        if op.ref in ctx.check_results:
            raise OperationRejected(f"O apelido de teste '{op.ref}' já foi usado.")
        ctx.check_results[op.ref] = result
    return result


def _roller(ctx: OperationContext, label: str, actor_id: str):
    """Rolador para fórmulas com roll("..."): também usa semente e fica registrado."""

    def roll_in_formula(notation: str) -> int:
        try:
            result = roll(notation, ctx.next_seed())
        except DiceSyntaxError as exc:
            raise ExpressionError(str(exc)) from None
        ctx.data.dice_rolls.record(notation, result.seed, result.total,
                                   {"formula_roll": result.to_dict(), "label": label, "actor_id": actor_id},
                                   ctx.turn_id)
        return result.total

    return roll_in_formula


def _value(raw, variables, roller, what: str) -> Decimal:
    try:
        return to_decimal(raw)
    except OperationRejected:
        pass
    try:
        value = evaluate(str(raw), variables, roller=roller)
    except ExpressionError as exc:
        raise OperationRejected(f"Fórmula do {what} inválida: {exc}") from None
    if not isinstance(value, Decimal):
        raise OperationRejected(f"O {what} precisa ser um número.")
    return value


HANDLERS = {"check.request": check_request}
