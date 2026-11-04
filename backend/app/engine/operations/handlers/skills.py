"""skill.grant / skill.revoke / skill.evolve."""

from __future__ import annotations

from decimal import Decimal

from app.engine.errors import OperationRejected
from app.engine.expressions import ExpressionError, evaluate
from app.engine.operations.context import OperationContext
from app.engine.operations.schemas import SkillEvolve, SkillGrant, SkillRevoke, SkillUse
from app.engine.rules.values import number_text, to_decimal
from app.engine.rules.variables import entity_variables
from app.engine.time import format_world_time, parse_duration
from app.persistence.models import EntitySkill


def _definition(ctx: OperationContext, key: str) -> dict:
    definition = ctx.data.definitions.current("skill", key)
    if definition is None:
        raise OperationRejected(f"A habilidade '{key}' não foi definida nesta campanha. Crie com definition.create.")
    return definition.data


def _check_level(definition: dict, level: int) -> None:
    max_level = definition.get("max_level")
    if max_level is not None and level > max_level:
        raise OperationRejected(f"{definition['name']} tem nível máximo {max_level}.")


def skill_grant(op: SkillGrant, ctx: OperationContext) -> dict:
    entity = ctx.entity(op.entity, allow_dead=False)
    definition = _definition(ctx, op.key)
    _check_level(definition, op.level)
    existing = ctx.data.skills.get_for(entity.id, op.key)
    if existing is not None and existing.active:
        raise OperationRejected(f"{entity.name} já tem {definition['name']}. Para melhorar, use skill.evolve.")
    if existing is not None:  # tinha perdido e recuperou
        existing.active, existing.level, existing.data = True, op.level, {**existing.data, **op.data}
        ctx.data.session.flush()
    else:
        ctx.data.skills.add(EntitySkill(entity_id=entity.id, definition_key=op.key, level=op.level, data=dict(op.data)))
    return {"entity_id": entity.id, "name": entity.name, "key": op.key, "skill": definition["name"], "level": op.level}


def skill_revoke(op: SkillRevoke, ctx: OperationContext) -> dict:
    entity = ctx.entity(op.entity)
    skill = ctx.data.skills.get_for(entity.id, op.key)
    if skill is None or not skill.active:
        raise OperationRejected(f"{entity.name} não tem a habilidade '{op.key}'.")
    skill.active = False  # guardada no histórico; pode ser recuperada
    ctx.data.session.flush()
    return {"entity_id": entity.id, "name": entity.name, "key": op.key, "level": skill.level}


def skill_evolve(op: SkillEvolve, ctx: OperationContext) -> dict:
    entity = ctx.entity(op.entity, allow_dead=False)
    definition = _definition(ctx, op.key)
    skill = ctx.data.skills.get_for(entity.id, op.key)
    if skill is None or not skill.active:
        raise OperationRejected(f"{entity.name} não tem {definition['name']} para evoluir.")
    new_level = skill.level + op.levels
    _check_level(definition, new_level)
    previous, skill.level = skill.level, new_level
    ctx.data.session.flush()
    return {"entity_id": entity.id, "name": entity.name, "key": op.key, "skill": definition["name"],
            "from": previous, "to": new_level}


def skill_use(op: SkillUse, ctx: OperationContext) -> dict:
    """Confere se pode usar e cobra os custos. Faltou recurso para algum custo: nada é cobrado."""
    entity = ctx.entity(op.entity, allow_dead=False)
    definition = _definition(ctx, op.key)
    skill = ctx.data.skills.get_for(entity.id, op.key)
    if skill is None or not skill.active:
        raise OperationRejected(f"{entity.name} não tem a habilidade {definition['name']}.")
    target = ctx.entity(op.target) if op.target else None
    variables = {**entity_variables(ctx.data, entity), "level": Decimal(skill.level)}
    now = ctx.data.campaign().world_clock
    ready_at = skill.data.get("ready_at")
    if ready_at is not None and now < ready_at:
        raise OperationRejected(
            f"{definition['name']} ainda está em recarga (pronta em {format_world_time(ready_at)})."
        )

    paid = []
    for cost in definition.get("costs", []):
        amount = _cost_amount(cost["amount"], variables, definition["name"])
        resource = ctx.data.attributes.get_for(entity.id, cost["resource"])
        if resource is None:
            raise OperationRejected(f"{entity.name} não tem {cost['resource']} para pagar {definition['name']}.")
        current = to_decimal(resource.value)
        if amount > current:
            raise OperationRejected(
                f"{entity.name} não tem {cost['resource']} suficiente para {definition['name']} "
                f"({resource.value} < {number_text(amount)})."
            )
        previous = resource.value
        ctx.data.attributes.upsert(entity.id, cost["resource"], number_text(current - amount))
        paid.append({"resource": cost["resource"], "amount": number_text(amount), "from": previous,
                     "to": number_text(current - amount), "max": resource.max_value})
    ready_text = None
    if definition.get("cooldown") is not None:
        next_ready = now + parse_duration(definition["cooldown"])
        skill.data = {**skill.data, "ready_at": next_ready}
        ctx.data.session.flush()
        ready_text = format_world_time(next_ready)
    return {"entity_id": entity.id, "name": entity.name, "key": op.key, "skill": definition["name"],
            "level": skill.level, "target_id": target.id if target else None,
            "target": target.name if target else None, "costs": paid, "ready_again": ready_text}


def _cost_amount(raw, variables, skill_name: str) -> Decimal:
    try:
        amount = to_decimal(raw)
    except OperationRejected:
        try:
            amount = evaluate(str(raw), variables)
        except ExpressionError as exc:
            raise OperationRejected(f"Custo de {skill_name} com fórmula inválida: {exc}") from None
        if not isinstance(amount, Decimal):
            raise OperationRejected(f"O custo de {skill_name} precisa ser um número.")
    if amount < 0:
        raise OperationRejected(f"O custo de {skill_name} não pode ser negativo.")
    return amount


HANDLERS = {"skill.grant": skill_grant, "skill.revoke": skill_revoke, "skill.evolve": skill_evolve,
            "skill.use": skill_use}
