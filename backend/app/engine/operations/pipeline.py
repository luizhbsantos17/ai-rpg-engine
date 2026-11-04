"""Pipeline: valida → aplica (cada operação no seu savepoint) → registra no log de eventos.

As operações são aplicadas em ordem, dentro da transação de quem chamou (o turno).
Uma operação inválida é recusada sozinha: o que ela fez é desfeito, o motivo vai para o
log (`operation.rejected`) e as próximas continuam. Assim uma resposta ruim da IA nunca
corrompe o estado (SPEC 20).
"""

from __future__ import annotations

import decimal
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from app.engine.errors import OperationRejected
from app.engine.operations.context import OperationContext
from app.engine.operations.handlers import HANDLERS
from app.engine.operations.schemas import parse_operation

logger = logging.getLogger(__name__)

MAX_OPERATIONS_PER_BATCH = 50
MAX_RAW_LOG_CHARS = 2000
# Dígitos significativos nas contas do motor. O padrão do Python (28) perderia a parte
# pequena de números enormes (12 + 1e40 viraria 1e40).
DECIMAL_PRECISION = 100


@dataclass
class OperationOutcome:
    index: int
    op: str
    status: str  # "applied" | "rejected"
    reason: str | None = None
    result: dict[str, Any] = field(default_factory=dict)
    event_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"index": self.index, "op": self.op, "status": self.status, "reason": self.reason,
                "result": self.result, "event_id": self.event_id}


def apply_operations(ctx: OperationContext, raw_operations: list[Any]) -> list[OperationOutcome]:
    outcomes: list[OperationOutcome] = []
    if len(raw_operations) > MAX_OPERATIONS_PER_BATCH:
        ignored = len(raw_operations) - MAX_OPERATIONS_PER_BATCH
        logger.warning("Lote com %d operações; %d ignoradas.", len(raw_operations), ignored)
    for index, raw in enumerate(raw_operations[:MAX_OPERATIONS_PER_BATCH]):
        outcomes.append(_apply_one(ctx, index, raw))
    return outcomes


def _apply_one(ctx: OperationContext, index: int, raw: Any) -> OperationOutcome:
    name = raw.get("op", "?") if isinstance(raw, dict) else "?"
    try:
        operation = parse_operation(raw)
    except ValidationError as exc:
        return _reject(ctx, index, str(name), raw, _schema_message(exc))

    handler = HANDLERS[operation.op]
    refs_before, checks_before = dict(ctx.refs), dict(ctx.check_results)
    try:
        with ctx.data.savepoint(), decimal.localcontext(prec=DECIMAL_PRECISION):
            result = handler(operation, ctx)
            event = ctx.data.events.record(
                operation.op, ctx.source,
                {"operation": operation.model_dump(mode="json"), "result": result},
                ctx.turn_id, ctx.world_time,
            )
    except OperationRejected as exc:
        # O savepoint desfez o banco; os apelidos criados pela operação também são desfeitos.
        ctx.refs, ctx.check_results = refs_before, checks_before
        return _reject(ctx, index, operation.op, raw, exc.reason)
    return OperationOutcome(index, operation.op, "applied", result=result, event_id=event.id)


def _reject(ctx: OperationContext, index: int, name: str, raw: Any, reason: str) -> OperationOutcome:
    raw_text = json.dumps(raw, ensure_ascii=False, default=str)[:MAX_RAW_LOG_CHARS]
    event = ctx.data.events.record(
        "operation.rejected", ctx.source, {"op": name, "reason": reason, "raw": raw_text},
        ctx.turn_id, ctx.world_time,
    )
    return OperationOutcome(index, name, "rejected", reason=reason, event_id=event.id)


def _schema_message(exc: ValidationError) -> str:
    parts = []
    for error in exc.errors()[:3]:
        where = ".".join(str(p) for p in error["loc"])
        parts.append(f"{where}: {error['msg']}" if where else error["msg"])
    return "Formato inválido — " + "; ".join(parts)
