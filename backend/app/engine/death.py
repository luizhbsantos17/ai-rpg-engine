"""Regras de morte por universo (SPEC 7.4), aplicadas pelo MOTOR.

Quando uma operação deixa o recurso vital (definido na regra de morte da campanha) de uma entidade
ativa em 0 ou menos, a regra vigente é aplicada na hora, dentro da mesma operação. A IA não pode
"salvar" o personagem mudando a regra depois: mudar a regra exige `definition.amend` com motivo e só
vale dali em diante. Sem regra de morte definida, o motor não aplica nada sozinho.
"""

from __future__ import annotations

from typing import Any

from app.engine.operations.context import OperationContext
from app.engine.rules.values import number_text, to_decimal
from app.engine.time import format_world_time, parse_duration
from app.persistence.models import Effect, Entity, ScheduledEvent

UNCONSCIOUS_EFFECT = "inconsciente"
# Operações que podem levar um recurso a zero, e onde o resultado guarda (entidade, chave, novo valor).
AFFECTING_OPS = ("attribute.set", "attribute.modify", "resource.spend", "skill.use")


def current_rule(ctx: OperationContext) -> tuple[str, dict[str, Any]] | None:
    rules = ctx.data.definitions.list_current("death_rule")
    return (rules[0].key, rules[0].data) if rules else None


def check_death(ctx: OperationContext, op: str, result: dict[str, Any]) -> dict[str, Any] | None:
    if op not in AFFECTING_OPS:
        return None
    rule = current_rule(ctx)
    if rule is None:
        return None
    key, data = rule
    vital = data["vital_resource"]
    if op == "skill.use":
        paid = [c for c in result.get("costs", []) if c["resource"] == vital]
        if not paid:
            return None
        value = paid[-1]["to"]
    elif result.get("key") == vital:
        value = result["to"]
    else:
        return None
    if to_decimal(value) > 0:
        return None
    entity = ctx.data.entities.get(result["entity_id"])
    if entity is None or entity.status != Entity.STATUS_ACTIVE:
        return None
    if ctx.data.effects.active_by_key(entity.id, UNCONSCIOUS_EFFECT) is not None:
        return None  # já está caído; a regra não se aplica duas vezes
    return _apply(ctx, entity, key, data)


def _apply(ctx: OperationContext, entity: Entity, rule_key: str, rule: dict[str, Any]) -> dict[str, Any]:
    mode = rule["mode"]
    now = ctx.data.campaign().world_clock
    outcome: dict[str, Any] = {"entity_id": entity.id, "name": entity.name, "rule": rule_key,
                               "rule_name": rule.get("name", rule_key), "mode": mode,
                               "description": rule.get("description", ""), "returns_at": None}
    revive_value = number_text(to_decimal(rule.get("revive_value", 1)))
    if mode in ("permanent", "reincarnation", "resurrection"):
        entity.status = Entity.STATUS_DEAD
    if mode == "unconscious":
        _ensure_unconscious_definition(ctx)
        ends = now + parse_duration(rule["revive_after"])
        ctx.data.effects.add(Effect(target_id=entity.id, definition_key=UNCONSCIOUS_EFFECT, starts_at=now, ends_at=ends))
        _schedule_return(ctx, entity, ends, f"{entity.name} recobra a consciência.",
                         [{"op": "attribute.set", "entity": entity.id, "key": rule["vital_resource"],
                           "value": revive_value}])
        outcome["returns_at"] = format_world_time(ends)
    elif mode == "resurrection":
        ends = now + parse_duration(rule["revive_after"])
        _schedule_return(ctx, entity, ends, f"{entity.name} volta à vida.", [
            {"op": "entity.update", "entity": entity.id, "status": "active", "reason": "regra de ressurreição"},
            {"op": "attribute.set", "entity": entity.id, "key": rule["vital_resource"], "value": revive_value},
        ])
        outcome["returns_at"] = format_world_time(ends)
    elif mode == "reincarnation":
        entity.data = {**entity.data, "reincarnation_pending": True}
    ctx.data.session.flush()
    return outcome


def _schedule_return(ctx: OperationContext, entity: Entity, due_at: int, summary: str, operations: list) -> None:
    ctx.data.schedule.add(ScheduledEvent(due_at=due_at, summary=summary, operations=operations, turn_id=ctx.turn_id))


def _ensure_unconscious_definition(ctx: OperationContext) -> None:
    if ctx.data.definitions.current("effect", UNCONSCIOUS_EFFECT) is None:
        ctx.data.definitions.create("effect", UNCONSCIOUS_EFFECT,
                                    {"name": "Inconsciente", "description": "Caído, sem poder agir."}, "system")
