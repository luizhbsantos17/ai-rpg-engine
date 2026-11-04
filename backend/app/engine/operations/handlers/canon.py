"""canon.assert / canon.amend — registro canônico com versões (SPEC 3.4)."""

from __future__ import annotations

from app.engine.errors import OperationRejected
from app.engine.operations.context import OperationContext
from app.engine.operations.schemas import CanonAmend, CanonAssert

CREATED_BY = {"ai": "ai", "admin": "admin"}


def canon_assert(op: CanonAssert, ctx: OperationContext) -> dict:
    existing = ctx.data.canon.current(op.key)
    if existing is not None:
        raise OperationRejected(
            f"Já existe o fato '{op.key}': \"{existing.statement}\". Para mudá-lo use canon.amend com um motivo."
        )
    fact = ctx.data.canon.assert_fact(op.key, op.subject, op.statement, op.status, CREATED_BY.get(ctx.source, "system"))
    return {"fact_id": fact.id, "key": op.key, "subject": op.subject, "statement": op.statement,
            "status": op.status, "version": 1}


def canon_amend(op: CanonAmend, ctx: OperationContext) -> dict:
    previous = ctx.data.canon.current(op.key)
    if previous is None:
        raise OperationRejected(f"Não existe o fato '{op.key}' para alterar. Use canon.assert.")
    if not op.reason:
        raise OperationRejected("Mudar um fato estabelecido exige um motivo (reason): o passado não é reescrito em silêncio.")
    if op.statement is None and op.status is None:
        raise OperationRejected("canon.amend sem nenhuma mudança (statement ou status).")
    fact = ctx.data.canon.amend(
        previous, op.statement or previous.statement, op.status or previous.status, op.reason,
        CREATED_BY.get(ctx.source, "system"),
    )
    return {"fact_id": fact.id, "key": op.key, "subject": fact.subject, "statement": fact.statement,
            "status": fact.status, "version": fact.version, "previous": previous.statement,
            "previous_status": previous.status}


HANDLERS = {"canon.assert": canon_assert, "canon.amend": canon_amend}
