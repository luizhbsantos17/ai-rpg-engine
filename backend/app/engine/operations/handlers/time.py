"""time.advance / event.schedule — relógio do mundo e acontecimentos agendados (SPEC 10.2–10.3)."""

from __future__ import annotations

from pydantic import ValidationError

from app.engine.errors import OperationRejected
from app.engine.operations.context import OperationContext
from app.engine.operations.schemas import EventSchedule, TimeAdvance, parse_operation
from app.engine.time import format_duration, format_world_time, parse_duration
from app.persistence.models import ScheduledEvent

# Campos de operações que guardam referências: apelidos da lista atual viram ids reais ao agendar
# (quando o acontecimento disparar, os apelidos desta lista já não existirão).
REFERENCE_FIELDS = ("entity", "target", "actor", "owner", "location", "to", "to_owner", "to_location", "item", "source")
FORBIDDEN_WHEN_SCHEDULED = ("time.advance",)


def time_advance(op: TimeAdvance, ctx: OperationContext) -> dict:
    if ctx.inside_schedule:
        raise OperationRejected("Um acontecimento agendado não pode avançar o tempo.")
    from app.engine.operations.pipeline import apply_operations  # import aqui: evita ciclo

    minutes = parse_duration(op.duration)
    campaign = ctx.data.campaign()
    start, end = campaign.world_clock, campaign.world_clock + minutes

    triggered = []
    for scheduled in ctx.data.schedule.due(end):
        scheduled.status = ScheduledEvent.STATUS_DONE
        child = ctx.child("system", scheduled.due_at, f"agendado:{scheduled.id}")
        outcomes = apply_operations(child, scheduled.operations)
        triggered.append({
            "schedule_id": scheduled.id, "summary": scheduled.summary, "due_at": scheduled.due_at,
            "due_text": format_world_time(scheduled.due_at), "outcomes": [o.to_dict() for o in outcomes],
        })

    expired = []
    for effect in ctx.data.effects.expiring(end):
        effect.active = False
        target = ctx.data.entities.get(effect.target_id)
        expired.append({"effect_id": effect.id, "key": effect.definition_key, "name": _effect_name(ctx, effect.definition_key),
                        "target_id": effect.target_id, "target": target.name if target else "?"})

    campaign.world_clock = end
    ctx.world_time = end
    ctx.data.session.flush()
    return {"from": start, "to": end, "minutes": minutes, "duration_text": format_duration(minutes),
            "from_text": format_world_time(start), "to_text": format_world_time(end),
            "triggered": triggered, "expired_effects": expired}


def event_schedule(op: EventSchedule, ctx: OperationContext) -> dict:
    minutes = parse_duration(op.after)
    operations = []
    for index, raw in enumerate(op.operations):
        try:
            parsed = parse_operation(raw)
        except ValidationError as exc:
            raise OperationRejected(f"Operação agendada nº {index + 1} inválida: {exc.errors()[0]['msg']}") from None
        if parsed.op in FORBIDDEN_WHEN_SCHEDULED:
            raise OperationRejected(f"Operação agendada nº {index + 1}: '{parsed.op}' não pode ser agendada.")
        operations.append(_resolve_refs(dict(raw), ctx))
    due_at = ctx.data.campaign().world_clock + minutes
    scheduled = ctx.data.schedule.add(ScheduledEvent(due_at=due_at, summary=op.summary, operations=operations,
                                                     turn_id=ctx.turn_id))
    return {"schedule_id": scheduled.id, "summary": op.summary, "due_at": due_at,
            "due_text": format_world_time(due_at), "operations": len(operations)}


def _resolve_refs(raw: dict, ctx: OperationContext) -> dict:
    for name in REFERENCE_FIELDS:
        value = raw.get(name)
        if isinstance(value, str) and value in ctx.refs:
            raw[name] = ctx.refs[value]
    return raw


def _effect_name(ctx: OperationContext, key: str) -> str:
    definition = ctx.data.definitions.current("effect", key)
    return definition.data.get("name", key) if definition else key


HANDLERS = {"time.advance": time_advance, "event.schedule": event_schedule}
