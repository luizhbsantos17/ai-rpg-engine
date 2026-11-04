"""definition.create / definition.amend — regras novas e mudanças versionadas."""

from __future__ import annotations

from app.engine.errors import OperationRejected
from app.engine.operations.context import OperationContext
from app.engine.operations.schemas import DefinitionAmend, DefinitionCreate
from app.engine.rules.definitions import validate_definition

CREATED_BY = {"ai": "ai", "admin": "admin"}


def definition_create(op: DefinitionCreate, ctx: OperationContext) -> dict:
    if ctx.data.definitions.current(op.kind, op.key) is not None:
        raise OperationRejected(
            f"Já existe '{op.key}' ({op.kind}). Para mudar a regra use definition.amend (cria nova versão)."
        )
    data = validate_definition(op.kind, op.data)
    definition = ctx.data.definitions.create(op.kind, op.key, data, CREATED_BY.get(ctx.source, "system"))
    return {"definition_id": definition.id, "kind": op.kind, "key": op.key, "version": 1, "name": data["name"]}


def definition_amend(op: DefinitionAmend, ctx: OperationContext) -> dict:
    previous = ctx.data.definitions.current(op.kind, op.key)
    if previous is None:
        raise OperationRejected(f"Não existe '{op.key}' ({op.kind}) para alterar. Use definition.create.")
    if not op.reason:
        raise OperationRejected("Mudanças de regra precisam de um motivo (reason): o passado não é reescrito em silêncio.")
    data = validate_definition(op.kind, op.data)
    definition = ctx.data.definitions.amend(previous, data, CREATED_BY.get(ctx.source, "system"))
    return {
        "definition_id": definition.id, "kind": op.kind, "key": op.key,
        "version": definition.version, "previous_version": previous.version, "name": data["name"],
    }


HANDLERS = {"definition.create": definition_create, "definition.amend": definition_amend}
