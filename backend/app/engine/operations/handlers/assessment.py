"""Avaliação, ocultação e falsificação (SPEC Parte 6).

Regra da avaliação (o MOTOR rola; a IA só define poder e o que se tenta descobrir):
    total = dados + poder de avaliação;   dificuldade = 10 + força da ocultação do campo
    margem = total - dificuldade
    margem >= 10                 -> verdade, "confirmed" (e percebe que havia ocultação)
    margem >= 0                  -> sem ocultação: verdade "confirmed"; com ocultação: verdade "partial"
    -5 <= margem < 0             -> "estimated": só uma aproximação (números arredondados)
    margem < -5                  -> com valor falso: ENGANADO (vê o valor falso, nível "false");
                                    sem valor falso: "unknown" (não descobre nada)
Uma rolagem por avaliação, registrada com semente. O resultado vira linhas em `knowledge` do observador.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.engine.dice import DiceSyntaxError, roll
from app.engine.errors import OperationRejected
from app.engine.expressions import ExpressionError, evaluate
from app.engine.operations.context import OperationContext
from app.engine.operations.schemas import DisguiseApply, DisguiseRemove, KnowledgeAssess
from app.engine.rules.values import number_text, to_decimal
from app.engine.rules.variables import check_variables, entity_variables
from app.persistence.models import Entity

BASE_DIFFICULTY = 10
CRITICAL_MARGIN = 10
ESTIMATE_MARGIN = -5


def disguise_apply(op: DisguiseApply, ctx: OperationContext) -> dict:
    entity = ctx.entity(op.entity)
    power = _number(op.power, entity_variables(ctx.data, entity), "poder de ocultação")
    disguise = ctx.data.disguises.upsert(entity.id, op.field, op.presented_value, number_text(power))
    return {"disguise_id": disguise.id, "entity_id": entity.id, "name": entity.name, "field": op.field,
            "presented_value": op.presented_value, "power": disguise.power, "falsified": op.presented_value is not None}


def disguise_remove(op: DisguiseRemove, ctx: OperationContext) -> dict:
    entity = ctx.entity(op.entity)
    disguise = next((d for d in ctx.data.disguises.active_for(entity.id) if d.field == op.field), None)
    if disguise is None:
        raise OperationRejected(f"{entity.name} não oculta '{op.field}'.")
    disguise.active = False
    ctx.data.session.flush()
    return {"entity_id": entity.id, "name": entity.name, "field": op.field}


def knowledge_assess(op: KnowledgeAssess, ctx: OperationContext) -> dict:
    observer = ctx.entity(op.observer, allow_dead=False)
    target = ctx.entity(op.target)
    if observer.id == target.id:
        raise OperationRejected("Para ver os próprios status não é preciso avaliar.")
    variables = check_variables(ctx.data, observer, target)
    power = _number(op.power, variables, "poder de avaliação")
    try:
        dice = roll(op.dice, ctx.next_seed())
    except DiceSyntaxError as exc:
        raise OperationRejected(f"Dados inválidos: {exc}") from None
    total = Decimal(dice.total) + power

    findings = [_assess_field(ctx, observer, target, field, total) for field in op.fields]
    detected = _detected(op, ctx, target, power)
    if detected:
        ctx.data.memories.remember(target.id, f"Percebeu que {observer.name} tentou avaliá-lo.", 3,
                                   ctx.world_time, ctx.turn_id)
    result = {"label": op.label, "observer_id": observer.id, "observer": observer.name,
              "target_id": target.id, "target": target.name, "dice": dice.to_dict(),
              "power": number_text(power), "total": number_text(total), "findings": findings, "detected": detected}
    ctx.data.dice_rolls.record(op.dice, dice.seed, dice.total, {"assessment": {**result, "findings": len(findings)}},
                               ctx.turn_id)
    return result


def _assess_field(ctx: OperationContext, observer: Entity, target: Entity, field: str, total: Decimal) -> dict[str, Any]:
    truth = _true_value(ctx, target, field)
    disguise = ctx.data.disguises.for_field(target.id, field)
    concealment = to_decimal(disguise.power) if disguise else Decimal(0)
    margin = total - (BASE_DIFFICULTY + concealment)

    if margin >= CRITICAL_MARGIN or (margin >= 0 and disguise is None):
        level, value = "confirmed", truth
    elif margin >= 0:
        level, value = "partial", truth
    elif margin >= ESTIMATE_MARGIN:
        level, value = "estimated", _estimate(truth)
    elif disguise is not None and disguise.presented_value is not None:
        level, value = "false", disguise.presented_value
    else:
        level, value = "unknown", None
    if value is not None or level == "unknown":
        ctx.data.knowledge.upsert(observer.id, target.id, field, value, level, "avaliou")
    return {"field": field, "level": level, "value": value, "truth": truth,
            "concealed": disguise is not None, "noticed_concealment": disguise is not None and margin >= CRITICAL_MARGIN,
            "margin": number_text(margin)}


def _true_value(ctx: OperationContext, target: Entity, field: str) -> str | None:
    if field == "identity":
        return str(target.data.get("true_identity") or target.name)
    if field == "skills":
        skills = ctx.data.skills.for_entity(target.id)
        return ", ".join(f"{s.definition_key} {s.level}" for s in skills) or "nenhuma"
    attribute = ctx.data.attributes.get_for(target.id, field)
    if attribute is None:
        raise OperationRejected(f"{target.name} não tem a informação '{field}' para ser avaliada.")
    return attribute.value + (f"/{attribute.max_value}" if attribute.max_value is not None else "")


def _estimate(truth: str | None) -> str | None:
    """Aproximação: números viram "≈" com 1 algarismo significativo; o resto vira "?"."""
    if truth is None:
        return None
    first = truth.split("/")[0]
    try:
        number = to_decimal(first)
    except OperationRejected:
        return "?"
    if number == 0:
        return "≈0"
    exponent = number.adjusted()  # 1234 -> 3
    rounded = number.scaleb(-exponent).quantize(Decimal(1)).scaleb(exponent)  # 1,234 -> 1 -> 1000
    return f"≈{number_text(rounded)}"


def _detected(op: KnowledgeAssess, ctx: OperationContext, target: Entity, observer_power: Decimal) -> bool:
    if op.detection is None:
        return False
    awareness = _number(op.detection, entity_variables(ctx.data, target), "percepção do alvo")
    check = roll("1d20", ctx.next_seed())
    ctx.data.dice_rolls.record("1d20", check.seed, check.total, {"assessment_detection": target.id}, ctx.turn_id)
    return Decimal(check.total) + awareness >= BASE_DIFFICULTY + observer_power


def _number(raw, variables, what: str) -> Decimal:
    try:
        return to_decimal(raw)
    except OperationRejected:
        pass
    try:
        value = evaluate(str(raw), variables)
    except ExpressionError as exc:
        raise OperationRejected(f"Fórmula do {what} inválida: {exc}") from None
    if not isinstance(value, Decimal):
        raise OperationRejected(f"O {what} precisa ser um número.")
    return value


HANDLERS = {"disguise.apply": disguise_apply, "disguise.remove": disguise_remove, "knowledge.assess": knowledge_assess}
