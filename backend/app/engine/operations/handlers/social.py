"""relationship.change — relações direcionais com dimensões livres e causa registrada (SPEC 9)."""

from __future__ import annotations

from app.engine.errors import OperationRejected
from app.engine.operations.context import OperationContext
from app.engine.operations.schemas import RelationshipChange

# Faixa de cada dimensão. Uma escala comum ajuda a IA a ser consistente entre turnos (D-031).
DIMENSION_MIN, DIMENSION_MAX = -100, 100
MAX_STEP = 50  # uma única mudança não vira amor eterno de uma vez
MAX_LABELS = 12


def relationship_change(op: RelationshipChange, ctx: OperationContext) -> dict:
    source = ctx.entity(op.source)
    target = ctx.entity(op.target)
    if source.id == target.id:
        raise OperationRejected("Uma relação precisa de duas entidades diferentes.")
    if not op.changes and not op.add_labels and not op.remove_labels:
        raise OperationRejected("relationship.change sem nenhuma mudança.")

    relationship = ctx.data.relationships.get_or_create(source.id, target.id)
    dimensions = dict(relationship.dimensions)
    changes = {}
    for dimension, delta in op.changes.items():
        if abs(delta) > MAX_STEP:
            raise OperationRejected(
                f"Mudança grande demais em '{dimension}' de uma vez ({delta}); o máximo é ±{MAX_STEP} por acontecimento."
            )
        before = dimensions.get(dimension, 0)
        after = max(DIMENSION_MIN, min(DIMENSION_MAX, before + delta))
        dimensions[dimension] = after
        changes[dimension] = {"from": before, "to": after, "delta": delta}

    labels = [label for label in relationship.labels if label not in op.remove_labels]
    labels += [label for label in op.add_labels if label not in labels]
    if len(labels) > MAX_LABELS:
        raise OperationRejected(f"No máximo {MAX_LABELS} rótulos por relação.")

    relationship.dimensions, relationship.labels = dimensions, labels
    ctx.data.session.flush()
    ctx.data.relationships.record_change(
        relationship, {"dimensions": changes, "added": op.add_labels, "removed": op.remove_labels},
        op.cause, ctx.turn_id, ctx.world_time,
    )
    return {"relationship_id": relationship.id, "source_id": source.id, "source": source.name,
            "target_id": target.id, "target": target.name, "changes": changes,
            "labels": labels, "added": op.add_labels, "removed": op.remove_labels, "cause": op.cause}


HANDLERS = {"relationship.change": relationship_change}
