"""skill.grant / skill.revoke / skill.evolve."""

from __future__ import annotations

from app.engine.errors import OperationRejected
from app.engine.operations.context import OperationContext
from app.engine.operations.schemas import SkillEvolve, SkillGrant, SkillRevoke
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


HANDLERS = {"skill.grant": skill_grant, "skill.revoke": skill_revoke, "skill.evolve": skill_evolve}
