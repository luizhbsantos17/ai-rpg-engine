"""quest.create / quest.update — missões com objetivos, ocultas ou visíveis (SPEC 10.1)."""

from __future__ import annotations

from app.engine.errors import OperationRejected
from app.engine.operations.context import OperationContext
from app.engine.operations.schemas import QuestCreate, QuestUpdate
from app.persistence.models import Quest

MAX_OBJECTIVES = 20


def quest_create(op: QuestCreate, ctx: OperationContext) -> dict:
    if ctx.data.quests.by_key(op.key) is not None:
        raise OperationRejected(f"Já existe a missão '{op.key}'. Para mudar, use quest.update.")
    giver = ctx.entity(op.giver) if op.giver else None
    quest = ctx.data.quests.add(Quest(
        key=op.key, title=op.title, kind=op.kind, description=op.description,
        giver_id=giver.id if giver else None, hidden=op.hidden,
        objectives=[{"text": text, "done": False} for text in op.objectives],
    ))
    return {"quest_id": quest.id, "key": op.key, "title": op.title, "kind": op.kind, "hidden": op.hidden,
            "giver": giver.name if giver else None, "objectives": list(op.objectives)}


def quest_update(op: QuestUpdate, ctx: OperationContext) -> dict:
    quest = ctx.data.quests.by_key(op.key)
    if quest is None:
        raise OperationRejected(f"Missão '{op.key}' não existe. Crie com quest.create.")
    if quest.status != "active" and op.status in (None, quest.status) and (op.complete_objectives or op.add_objectives):
        raise OperationRejected(f"A missão '{quest.title}' já terminou ({quest.status}).")

    objectives = [dict(o) for o in quest.objectives]
    completed = []
    for number in op.complete_objectives:
        if not 1 <= number <= len(objectives):
            raise OperationRejected(f"A missão '{quest.title}' não tem o objetivo nº {number}.")
        if not objectives[number - 1]["done"]:
            objectives[number - 1]["done"] = True
            completed.append(objectives[number - 1]["text"])
    objectives += [{"text": text, "done": False} for text in op.add_objectives]
    if len(objectives) > MAX_OBJECTIVES:
        raise OperationRejected(f"No máximo {MAX_OBJECTIVES} objetivos por missão.")

    previous_status, revealed = quest.status, op.reveal and quest.hidden
    quest.objectives = objectives
    if op.status is not None:
        quest.status = op.status
    if op.reveal:
        quest.hidden = False
    if not (completed or op.add_objectives or op.status not in (None, previous_status) or revealed):
        raise OperationRejected("quest.update sem nenhuma mudança.")
    ctx.data.session.flush()
    return {"quest_id": quest.id, "key": op.key, "title": quest.title, "hidden": quest.hidden,
            "status": quest.status, "previous_status": previous_status, "completed_objectives": completed,
            "added_objectives": list(op.add_objectives), "revealed": revealed}


HANDLERS = {"quest.create": quest_create, "quest.update": quest_update}
