"""Variáveis que as fórmulas podem usar sobre uma entidade.

Para o ator: `forca` (atributos pelo nome-chave), `vida_max` (máximo de recursos),
`skills.bola_de_fogo` (nível da habilidade) e as mesmas coisas com prefixo `actor.`.
Para o alvo: `target.forca`, `target.skills.esquiva`...
Itens equipados somam o "bonus" da definição ao atributo (`defesa` já inclui o escudo; `defesa_base` não).
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.errors import OperationRejected
from app.engine.rules.values import to_decimal
from app.persistence.models import Entity
from app.persistence.repositories import CampaignData

EQUIPPED_FIELD = "equipped_slot"  # mesmo nome usado por item.equip


def entity_variables(data: CampaignData, entity: Entity) -> dict[str, object]:
    values: dict[str, object] = {}
    for attribute in data.attributes.for_entity(entity.id):
        values[attribute.definition_key] = _number_or_text(attribute.value)
        if attribute.max_value is not None:
            values[f"{attribute.definition_key}_max"] = _number_or_text(attribute.max_value)
    for skill in data.skills.for_entity(entity.id):
        values[f"skills.{skill.definition_key}"] = Decimal(skill.level)
    for key, bonus in equipment_bonus(data, entity).items():
        base = values.get(key, Decimal(0))
        if isinstance(base, Decimal):  # atributo de texto (ex.: "nobre") não recebe bônus numérico
            values[f"{key}_base"] = base
            values[key] = base + bonus
    return values


def equipment_bonus(data: CampaignData, entity: Entity) -> dict[str, Decimal]:
    """Soma do "bonus" ({atributo: número}) das definições dos itens equipados pela entidade."""
    total: dict[str, Decimal] = {}
    for item in data.items.held_by(entity.id):
        if not item.data.get(EQUIPPED_FIELD):
            continue
        definition = data.definitions.current("item", item.definition_key)
        bonus = (definition.data.get("bonus") if definition else None) or {}
        for key, raw in bonus.items() if isinstance(bonus, dict) else ():
            try:
                total[key] = total.get(key, Decimal(0)) + to_decimal(str(raw))
            except OperationRejected:
                continue  # bônus que não é número é só descrição
    return total


def check_variables(data: CampaignData, actor: Entity, target: Entity | None) -> dict[str, object]:
    actor_values = entity_variables(data, actor)
    variables = dict(actor_values)
    variables.update({f"actor.{k}": v for k, v in actor_values.items()})
    if target is not None:
        variables.update({f"target.{k}": v for k, v in entity_variables(data, target).items()})
    return variables


def _number_or_text(raw: str) -> object:
    try:
        return to_decimal(raw)
    except OperationRejected:
        return raw
