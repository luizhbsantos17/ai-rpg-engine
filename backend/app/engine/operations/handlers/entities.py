"""entity.create / update / remove / move."""

from __future__ import annotations

from app.engine.errors import OperationRejected
from app.engine.operations.context import OperationContext
from app.engine.operations.handlers.attributes import write_initial_attribute
from app.engine.operations.schemas import EntityCreate, EntityMove, EntityRemove, EntityUpdate
from app.persistence.models import Entity

MAX_LOCATION_DEPTH = 50
DEFAULT_SIM_TIER = 2


def entity_create(op: EntityCreate, ctx: OperationContext) -> dict:
    if op.is_player and ctx.data.entities.player() is not None:
        raise OperationRejected("A campanha já tem um protagonista.")
    location = ctx.entity(op.location) if op.location else None
    # Padrão: protagonista em cena (0); os demais "distantes" (2) até a IA marcá-los como relevantes (1).
    sim_tier = op.sim_tier if op.sim_tier is not None else (0 if op.is_player else DEFAULT_SIM_TIER)
    entity = ctx.data.entities.add(
        Entity(
            kind=op.kind, name=op.name, is_player=op.is_player, data=dict(op.data),
            location_id=location.id if location else None, sim_tier=sim_tier,
        )
    )
    ctx.register_ref(op.ref, entity.id)
    attributes = {key: write_initial_attribute(ctx, entity, key, raw) for key, raw in op.attributes.items()}
    return {"entity_id": entity.id, "name": entity.name, "kind": entity.kind, "attributes": attributes}


def entity_update(op: EntityUpdate, ctx: OperationContext) -> dict:
    entity = ctx.entity(op.entity)
    changes: dict = {}
    if op.name is not None and op.name != entity.name:
        changes["name"] = {"from": entity.name, "to": op.name}
        entity.name = op.name
    if op.status is not None and op.status != entity.status:
        changes["status"] = {"from": entity.status, "to": op.status}
        entity.status = op.status
    if op.data:
        entity.data = {**entity.data, **op.data}
        changes["data"] = sorted(op.data)
    if op.sim_tier is not None and op.sim_tier != entity.sim_tier:
        changes["sim_tier"] = {"from": entity.sim_tier, "to": op.sim_tier}
        entity.sim_tier = op.sim_tier
    if not changes:
        raise OperationRejected("entity.update sem nenhuma mudança.")
    ctx.data.session.flush()
    return {"entity_id": entity.id, "name": entity.name, "changes": changes}


def entity_remove(op: EntityRemove, ctx: OperationContext) -> dict:
    entity = ctx.entity(op.entity)
    if entity.is_player:
        raise OperationRejected("O protagonista não pode ser removido. Para morte, use entity.update com status 'dead'.")
    entity.status = Entity.STATUS_REMOVED
    ctx.data.session.flush()
    return {"entity_id": entity.id, "name": entity.name}


def entity_move(op: EntityMove, ctx: OperationContext) -> dict:
    entity = ctx.entity(op.entity)
    destination = ctx.entity(op.to)
    if destination.id == entity.id:
        raise OperationRejected("Uma entidade não pode estar dentro de si mesma.")
    _reject_cycle(ctx, entity, destination)
    previous = entity.location_id
    entity.location_id = destination.id
    ctx.data.session.flush()
    return {"entity_id": entity.id, "name": entity.name, "from": previous, "to": destination.id, "to_name": destination.name}


def _reject_cycle(ctx: OperationContext, entity: Entity, destination: Entity) -> None:
    current, depth = destination, 0
    while current.location_id and depth < MAX_LOCATION_DEPTH:
        if current.location_id == entity.id:
            raise OperationRejected(f"'{destination.name}' fica dentro de '{entity.name}': o movimento criaria um ciclo.")
        current = ctx.data.entities.get(current.location_id)
        if current is None:
            return
        depth += 1


HANDLERS = {
    "entity.create": entity_create,
    "entity.update": entity_update,
    "entity.remove": entity_remove,
    "entity.move": entity_move,
}
