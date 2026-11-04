"""item.create / transfer / destroy / equip / unequip — sem duplicação: cada item tem um só lugar.

Equipado = `data["equipped_slot"]` do item. Um item por espaço por dono; ao mudar de dono, deixa de estar equipado.
"""

from __future__ import annotations

from app.engine.errors import OperationRejected
from app.engine.operations.context import OperationContext
from app.engine.operations.schemas import ItemCreate, ItemDestroy, ItemEquip, ItemTransfer, ItemUnequip
from app.engine.rules.variables import EQUIPPED_FIELD as EQUIPPED
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
    was_equipped = item.data.get(EQUIPPED)
    if quantity == item.quantity:
        item.owner_id, item.location_id = owner_id, location_id
        item.data = _unequipped(item.data)
        ctx.data.session.flush()
        moved = item
    else:
        item.quantity -= quantity
        ctx.data.session.flush()
        moved = _place(ctx, item.definition_key, owner_id, location_id, quantity, _unequipped(item.data),
                       definition.get("stackable", True))
    result = {"item_id": moved.id, "source_item_id": item.id, "item": definition["name"],
              "quantity": quantity, "to": holder.name, "to_id": holder.id, "from_id": from_id}
    if was_equipped and moved is item:
        result["unequipped_slot"] = was_equipped
    return result


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


def item_equip(op: ItemEquip, ctx: OperationContext) -> dict:
    item = ctx.item(op.item)
    definition = _definition(ctx, item.definition_key)
    if item.owner_id is None:
        raise OperationRejected(f"{definition['name']} está no chão: só dá para equipar um item que alguém carrega.")
    owner = ctx.entity(item.owner_id, allow_dead=False)
    fixed_slot = definition.get("slot")
    slot = op.slot or fixed_slot
    if not slot:
        raise OperationRejected(f"{definition['name']} não tem espaço de equipamento: informe slot "
                                "(ou defina \"slot\" no item com definition.amend).")
    if fixed_slot and slot != fixed_slot:
        raise OperationRejected(f"{definition['name']} só pode ser equipado em '{fixed_slot}'.")
    if item.data.get(EQUIPPED) == slot:
        raise OperationRejected(f"{definition['name']} já está equipado em '{slot}'.")
    replaced = next((other for other in ctx.data.items.held_by(owner.id)
                     if other.id != item.id and other.data.get(EQUIPPED) == slot), None)
    if replaced is not None:
        replaced.data = _unequipped(replaced.data)
    item.data = {**item.data, EQUIPPED: slot}
    ctx.data.session.flush()
    result = {"item_id": item.id, "item": definition["name"], "slot": slot, "owner": owner.name,
              "owner_id": owner.id, "bonus": definition.get("bonus") or {}}
    if replaced is not None:
        result["replaced"] = _definition(ctx, replaced.definition_key)["name"]
        result["replaced_item_id"] = replaced.id
    return result


def item_unequip(op: ItemUnequip, ctx: OperationContext) -> dict:
    item = ctx.item(op.item)
    definition = _definition(ctx, item.definition_key)
    slot = item.data.get(EQUIPPED)
    if not slot:
        raise OperationRejected(f"{definition['name']} não está equipado.")
    item.data = _unequipped(item.data)
    ctx.data.session.flush()
    owner = ctx.data.entities.get(item.owner_id) if item.owner_id else None
    return {"item_id": item.id, "item": definition["name"], "slot": slot,
            "owner": owner.name if owner else None, "owner_id": item.owner_id}


def _unequipped(data: dict) -> dict:
    """Cópia sem a marca de equipado (o JSON precisa de um objeto novo para o banco perceber a mudança)."""
    return {k: v for k, v in data.items() if k != EQUIPPED}


HANDLERS = {"item.create": item_create, "item.transfer": item_transfer, "item.destroy": item_destroy,
            "item.equip": item_equip, "item.unequip": item_unequip}
