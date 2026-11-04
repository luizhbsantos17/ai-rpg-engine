"""effect.apply / effect.remove — efeitos com duração no tempo do mundo."""

from __future__ import annotations

from app.engine.errors import OperationRejected
from app.engine.operations.context import OperationContext
from app.engine.operations.schemas import EffectApply, EffectRemove
from app.engine.rules.values import number_text, to_decimal
from app.engine.time import format_world_time, parse_duration
from app.persistence.models import Effect


def _definition(ctx: OperationContext, key: str) -> dict:
    definition = ctx.data.definitions.current("effect", key)
    if definition is None:
        raise OperationRejected(f"O efeito '{key}' não foi definido nesta campanha. Crie com definition.create (kind effect).")
    return definition.data


def effect_apply(op: EffectApply, ctx: OperationContext) -> dict:
    target = ctx.entity(op.target)
    definition = _definition(ctx, op.key)
    source = ctx.entity(op.source) if op.source else None
    now = ctx.data.campaign().world_clock
    ends_at = now + parse_duration(op.duration) if op.duration is not None else None
    intensity = number_text(to_decimal(op.intensity)) if op.intensity is not None else None

    effect = ctx.data.effects.active_by_key(target.id, op.key)
    refreshed = effect is not None
    if refreshed:  # o mesmo efeito de novo: renova em vez de duplicar
        effect.ends_at, effect.intensity = ends_at, intensity or effect.intensity
        ctx.data.session.flush()
    else:
        effect = ctx.data.effects.add(Effect(
            target_id=target.id, definition_key=op.key, source_id=source.id if source else None,
            intensity=intensity, starts_at=now, ends_at=ends_at,
        ))
    return {"effect_id": effect.id, "entity_id": target.id, "name": target.name, "key": op.key,
            "effect": definition["name"], "ends_at": ends_at,
            "ends_text": format_world_time(ends_at) if ends_at is not None else None,
            "intensity": intensity, "refreshed": refreshed}


def effect_remove(op: EffectRemove, ctx: OperationContext) -> dict:
    target = ctx.entity(op.target)
    effect = ctx.data.effects.active_by_key(target.id, op.key)
    if effect is None:
        raise OperationRejected(f"{target.name} não está sob o efeito '{op.key}'.")
    effect.active = False
    ctx.data.session.flush()
    definition = ctx.data.definitions.current("effect", op.key)
    return {"effect_id": effect.id, "entity_id": target.id, "name": target.name, "key": op.key,
            "effect": definition.data.get("name", op.key) if definition else op.key}


HANDLERS = {"effect.apply": effect_apply, "effect.remove": effect_remove}
