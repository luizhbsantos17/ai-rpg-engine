"""Aplicadores das operações. Cada um valida as regras e altera o estado pelos repositórios.

Todos recebem (operação, contexto) e devolvem um dicionário com o resultado, que vai para
o log de eventos e para a IA narrar. Se a operação for inválida: `raise OperationRejected`.
"""

from app.engine.operations.handlers import (
    attributes,
    canon,
    checks,
    definitions,
    effects,
    entities,
    items,
    knowledge,
    narrative,
    quests,
    skills,
    social,
    time,
)

HANDLERS = {
    **social.HANDLERS,
    **knowledge.HANDLERS,
    **quests.HANDLERS,
    **time.HANDLERS,
    **effects.HANDLERS,
    **definitions.HANDLERS,
    **entities.HANDLERS,
    **attributes.HANDLERS,
    **skills.HANDLERS,
    **items.HANDLERS,
    **checks.HANDLERS,
    **canon.HANDLERS,
    **narrative.HANDLERS,
}
