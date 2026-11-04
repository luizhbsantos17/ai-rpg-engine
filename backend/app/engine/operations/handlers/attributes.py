"""attribute.set / attribute.modify / resource.spend / resource.restore."""

from __future__ import annotations

from decimal import Decimal

from app.engine.errors import OperationRejected
from app.engine.expressions import ExpressionError, evaluate
from app.engine.operations.context import OperationContext
from app.engine.operations.schemas import (
    AttributeModify,
    AttributeSet,
    AttributeValue,
    ResourceRestore,
    ResourceSpend,
)
from app.engine.rules.definitions import AttributeDefinition, attribute_definition
from app.engine.rules.values import check_bounds, normalize_value, number_text, to_decimal
from app.engine.rules.variables import entity_variables
from app.persistence.models import Entity


def _definition(ctx: OperationContext, key: str) -> AttributeDefinition:
    definition = ctx.data.definitions.current("attribute", key)
    if definition is None:
        raise OperationRejected(f"O atributo '{key}' não foi definido nesta campanha. Crie com definition.create.")
    return attribute_definition(definition.data)


def write_initial_attribute(ctx: OperationContext, entity: Entity, key: str, raw) -> dict:
    """Valor inicial de um atributo na criação da entidade."""
    definition = _definition(ctx, key)
    value_raw, max_raw = (raw.value, raw.max) if isinstance(raw, AttributeValue) else (raw, None)
    value = normalize_value(definition, value_raw)
    max_value = None
    if definition.resource:
        max_value = normalize_value(definition, max_raw if max_raw is not None else value_raw)
        if to_decimal(value) > to_decimal(max_value):
            raise OperationRejected(f"{definition.name}: o valor atual não pode passar do máximo.")
    elif max_raw is not None:
        raise OperationRejected(f"{definition.name} não é um recurso; não tem máximo.")
    ctx.data.attributes.upsert(entity.id, key, value, max_value)
    return {"value": value, "max": max_value} if max_value is not None else {"value": value}


def attribute_set(op: AttributeSet, ctx: OperationContext) -> dict:
    entity = ctx.entity(op.entity)
    definition = _definition(ctx, op.key)
    current = ctx.data.attributes.get_for(entity.id, op.key)
    value = normalize_value(definition, op.value)
    max_value = None
    if definition.resource:
        max_value = normalize_value(definition, op.max) if op.max is not None else (current.max_value if current else value)
        if to_decimal(value) > to_decimal(max_value):
            raise OperationRejected(f"{definition.name}: o valor atual não pode passar do máximo ({max_value}).")
    elif op.max is not None:
        raise OperationRejected(f"{definition.name} não é um recurso; não tem máximo.")
    previous = current.value if current else None  # ler ANTES de gravar (o registro é o mesmo objeto)
    ctx.data.attributes.upsert(entity.id, op.key, value, max_value)
    return {
        "entity_id": entity.id, "name": entity.name, "key": op.key, "attribute": definition.name,
        "from": previous, "to": value, "max": max_value,
    }


def attribute_modify(op: AttributeModify, ctx: OperationContext) -> dict:
    entity = ctx.entity(op.entity)
    definition = _definition(ctx, op.key)
    if definition.value_type not in ("integer", "decimal"):
        raise OperationRejected(f"{definition.name} não é numérico; use attribute.set.")
    current = ctx.data.attributes.get_for(entity.id, op.key)
    if current is None:
        raise OperationRejected(f"{entity.name} não tem o atributo {definition.name}; use attribute.set primeiro.")
    delta = _amount(op.delta, ctx, entity)
    previous = current.value
    old = to_decimal(previous)
    new, clamped = _clamped(definition, old + delta, current.max_value)
    if definition.value_type == "integer":
        new = new.to_integral_value()
    ctx.data.attributes.upsert(entity.id, op.key, number_text(new))
    return {
        "entity_id": entity.id, "name": entity.name, "key": op.key, "attribute": definition.name,
        "from": previous, "to": number_text(new), "delta": number_text(delta), "clamped": clamped,
        "max": current.max_value,
    }


def resource_spend(op: ResourceSpend, ctx: OperationContext) -> dict:
    entity, definition, current = _resource(op.entity, op.key, ctx)
    amount = _positive(op.amount, ctx, entity)
    previous = current.value
    old = to_decimal(previous)
    if amount > old:
        raise OperationRejected(f"{entity.name} não tem {definition.name} suficiente ({current.value} < {number_text(amount)}).")
    new = old - amount
    ctx.data.attributes.upsert(entity.id, op.key, number_text(new))
    return {"entity_id": entity.id, "name": entity.name, "key": op.key, "attribute": definition.name,
            "from": previous, "to": number_text(new), "spent": number_text(amount), "max": current.max_value}


def resource_restore(op: ResourceRestore, ctx: OperationContext) -> dict:
    entity, definition, current = _resource(op.entity, op.key, ctx)
    amount = _positive(op.amount, ctx, entity)
    previous = current.value
    old = to_decimal(previous)
    new = min(old + amount, to_decimal(current.max_value))
    ctx.data.attributes.upsert(entity.id, op.key, number_text(new))
    return {"entity_id": entity.id, "name": entity.name, "key": op.key, "attribute": definition.name,
            "from": previous, "to": number_text(new), "restored": number_text(new - old), "max": current.max_value}


def _resource(ref: str, key: str, ctx: OperationContext):
    entity = ctx.entity(ref)
    definition = _definition(ctx, key)
    if not definition.resource:
        raise OperationRejected(f"{definition.name} não é um recurso; use attribute.modify.")
    current = ctx.data.attributes.get_for(entity.id, key)
    if current is None:
        raise OperationRejected(f"{entity.name} não tem {definition.name}.")
    return entity, definition, current


def _amount(raw, ctx: OperationContext, entity: Entity) -> Decimal:
    """Número direto ou fórmula calculada com os atributos da própria entidade."""
    try:
        return to_decimal(raw)
    except OperationRejected:
        pass
    try:
        result = evaluate(str(raw), entity_variables(ctx.data, entity))
    except ExpressionError as exc:
        raise OperationRejected(f"Fórmula inválida: {exc}") from None
    if not isinstance(result, Decimal):
        raise OperationRejected("A fórmula precisa resultar em um número.")
    return result


def _positive(raw, ctx: OperationContext, entity: Entity) -> Decimal:
    amount = _amount(raw, ctx, entity)
    if amount <= 0:
        raise OperationRejected("A quantidade precisa ser maior que zero.")
    return amount


def _clamped(definition: AttributeDefinition, value: Decimal, max_value: str | None) -> tuple[Decimal, bool]:
    """Mantém o valor dentro dos limites declarados (e do máximo, para recursos)."""
    low = to_decimal(definition.min) if definition.min is not None else (Decimal(0) if definition.resource else None)
    high_candidates = [to_decimal(v) for v in (definition.max, max_value) if v is not None]
    high = min(high_candidates) if high_candidates else None
    if low is not None and value < low:
        return low, True
    if high is not None and value > high:
        return high, True
    check_bounds(definition, value)
    return value, False


HANDLERS = {
    "attribute.set": attribute_set,
    "attribute.modify": attribute_modify,
    "resource.spend": resource_spend,
    "resource.restore": resource_restore,
}
