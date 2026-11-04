"""knowledge.record / memory.record — o que cada um sabe e lembra (SPEC 6.5, 8.2)."""

from __future__ import annotations

from app.engine.errors import OperationRejected
from app.engine.operations.context import PLAYER_REF, OperationContext
from app.engine.operations.schemas import KnowledgeRecord, MemoryRecord


def knowledge_record(op: KnowledgeRecord, ctx: OperationContext) -> dict:
    observer = ctx.entity(op.observer)
    subject_id, subject_name = _subject(op.subject, ctx)
    if subject_id == observer.id and op.level == "false":
        raise OperationRejected("Uma entidade não pode ter conhecimento falso sobre si mesma por este meio.")
    record = ctx.data.knowledge.upsert(observer.id, subject_id, op.field, op.value, op.level, op.source)
    return {"knowledge_id": record.id, "observer_id": observer.id, "observer": observer.name,
            "subject": subject_id, "subject_name": subject_name, "field": op.field, "value": op.value,
            "level": op.level, "source": op.source}


def memory_record(op: MemoryRecord, ctx: OperationContext) -> dict:
    entity = ctx.entity(op.entity)
    memory = ctx.data.memories.remember(entity.id, op.content, op.importance, ctx.world_time, ctx.turn_id)
    return {"memory_id": memory.id, "entity_id": entity.id, "name": entity.name,
            "content": op.content, "importance": op.importance}


def _subject(ref: str, ctx: OperationContext) -> tuple[str, str]:
    """Entidade (por "player", apelido ou id) ou um tema livre."""
    if ref == PLAYER_REF or ref in ctx.refs or ctx.data.entities.get(ref) is not None:
        entity = ctx.entity(ref)
        return entity.id, entity.name
    return ref, ref


HANDLERS = {"knowledge.record": knowledge_record, "memory.record": memory_record}
