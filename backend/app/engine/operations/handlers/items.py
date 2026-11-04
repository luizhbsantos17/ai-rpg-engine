"""item.create / item.transfer / item.destroy — sem duplicação: cada item tem um só lugar."""

from __future__ import annotations

from app.engine.errors import OperationRejected
from app.engine.operations.context import OperationContext
from app.engine.operations.schemas import ItemCreate, ItemDestroy, ItemTransfer
from app.persistence.models import ItemInstance


def _definition(ctx: OperationContext, key: str) -> dict:
    definition = ctx.data.definitions.current("item", key)
    if definition is None:
        raise OperationRejected(f"O item '{key}' não foi definido nesta campanha. Crie com definition.create.")
    return definition.data


def _holder(ctx: OperationContext, owner: str | None, location: str | None):
    """Devolve (owner_id, location_id, entidade de destino)."""
    if (owner is None) == (location is None):
        raise OperationRejected("Informe exatamente um destino: um dono OU um local.")
    entity = ctx.entity(owner or location)
    return (entity.id, None, entity) if owner else (None, entity.id, entity)


def _place(ctx: OperationContext, key: str, owner_id, location_id, quantity: int, data: dict, stackable: bool) -> ItemInstance:
    """Junta à pilha existente do mesmo item no mesmo lugar (se empilhável) ou cria um novo."""
    if stackable and not data:
        holders = ctx.data.items.held_by(owner_id) if owner_id else ctx.data.items.at_location(location_id)
        for existing in holders:
            if existing.definition_key == key and not existing.data:
                existing.quantity += quantity
                ctx.data.session.flush()
                return existing
    return ctx.data.items.add(
        ItemInstance(definition_key=key, owner_id=owner_id, location_id=location_id, quantity=quantity, data=dict(data))
    )


def item_create(op: ItemCreate, ctx: OperationContext) -> dict:
    definition = _definition(ctx, op.key)
    stackable = definition.get("stackable", True)
    if not stackable and op.quantity != 1:
        raise OperationRejected(f"{definition['name']} não é empilhável: crie um de cada vez.")
    owner_id, location_id, holder = _holder(ctx, op.owner, op.location)
    item = _place(ctx, op.key, owner_id, location_id, op.quantity, op.data, stackable)
    ctx.register_ref(op.ref, item.id)
    return {"item_id": item.id, "key": op.key, "item": definition["name"], "quantity": op.quantity,
            "holder": holder.name, "holder_id": holder.id, "total_quantity": item.quantity}


def item_transfer(op: ItemTransfer, ctx: OperationContext) -> dict:
    item = ctx.item(op.item)
    definition = _definition(ctx, item.definition_key)
    owner_id, location_id, holder = _holder(ctx, op.to_owner, op.to_location)
    from_id = item.owner_id or item.location_id
    if (owner_id, location_id) == (item.owner_id, item.location_id):
        raise OperationRejected("O item já está nesse lugar.")
    quantity = op.quantity or item.quantity
    if quantity > item.quantity:
        raise OperationRejected(f"Só há {item.quantity} de {definition['name']} para transferir.")
    if quantity == item.quantity:
        item.owner_id, item.location_id = owner_id, location_id
        ctx.data.session.flush()
        moved = item
    else:
        item.quantity -= quantity
        ctx.data.session.flush()
        moved = _place(ctx, item.definition_key, owner_id, location_id, quantity, dict(item.data),
                       definition.get("stackable", True))
    return {"item_id": moved.id, "source_item_id": item.id, "item": definition["name"],
            "quantity": quantity, "to": holder.name, "to_id": holder.id, "from_id": from_id}


def item_destroy(op: ItemDestroy, ctx: OperationContext) -> dict:
    item = ctx.item(op.item)
    definition = _definition(ctx, item.definition_key)
    quantity = op.quantity or item.quantity
    if quantity > item.quantity:
        raise OperationRejected(f"Só há {item.quantity} de {definition['name']}.")
    item.quantity -= quantity
    if item.quantity == 0:
        item.quantity = quantity  # guarda quanto havia; o status marca a destruição
        item.status = ItemInstance.STATUS_DESTROYED
    ctx.data.session.flush()
    return {"item_id": item.id, "item": definition["name"], "destroyed": quantity,
            "remaining": 0 if item.status == ItemInstance.STATUS_DESTROYED else item.quantity}


HANDLERS = {"item.create": item_create, "item.transfer": item_transfer, "item.destroy": item_destroy}
