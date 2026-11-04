"""event.record — acontecimento importante sem mudança mecânica (fica no histórico)."""

from __future__ import annotations

from app.engine.operations.context import OperationContext
from app.engine.operations.schemas import EventRecord


def event_record(op: EventRecord, ctx: OperationContext) -> dict:
    entities = [ctx.entity(ref) for ref in op.entities]
    return {
        "summary": op.summary,
        "entities": [{"id": e.id, "name": e.name} for e in entities],
        "data": op.data,
    }


HANDLERS = {"event.record": event_record}
