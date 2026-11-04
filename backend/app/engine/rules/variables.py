"""Variáveis que as fórmulas podem usar sobre uma entidade.

Para o ator: `forca` (atributos pelo nome-chave), `vida_max` (máximo de recursos),
`skills.bola_de_fogo` (nível da habilidade) e as mesmas coisas com prefixo `actor.`.
Para o alvo: `target.forca`, `target.skills.esquiva`...
"""

from __future__ import annotations

from decimal import Decimal

from app.engine.errors import OperationRejected
from app.engine.rules.values import to_decimal
from app.persistence.models import Entity
from app.persistence.repositories import CampaignData


def entity_variables(data: CampaignData, entity: Entity) -> dict[str, object]:
    values: dict[str, object] = {}
    for attribute in data.attributes.for_entity(entity.id):
        values[attribute.definition_key] = _number_or_text(attribute.value)
        if attribute.max_value is not None:
            values[f"{attribute.definition_key}_max"] = _number_or_text(attribute.max_value)
    for skill in data.skills.for_entity(entity.id):
        values[f"skills.{skill.definition_key}"] = Decimal(skill.level)
    return values


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
