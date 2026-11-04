"""Resposta da IA na preparação da campanha: sistema de atributos, protagonista e local inicial.

Formato próprio e simples (mais fácil para modelos pequenos do que operações livres).
O motor converte em operações (`to_operations`), que passam pela validação normal.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SetupAttribute(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(min_length=1, max_length=100)
    value_type: Literal["integer", "decimal", "nominal", "conceptual"] = "integer"
    resource: bool = Field(default=False, description="true para vida, mana, energia...")
    description: str = Field(default="", max_length=500)
    initial_value: int | float | str = Field(description="valor inicial do protagonista")


class SetupProtagonist(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(min_length=1, max_length=200)
    kind: str = Field(default="character", max_length=40)
    description: str = Field(default="", max_length=2000)


class CampaignSetup(BaseModel):
    model_config = ConfigDict(extra="ignore")
    attributes: list[SetupAttribute] = Field(min_length=1, max_length=12)
    protagonist: SetupProtagonist
    starting_location: str = Field(min_length=1, max_length=200)
    location_description: str = Field(default="", max_length=2000)

    def to_operations(self) -> list[dict[str, Any]]:
        operations: list[dict[str, Any]] = []
        values: dict[str, Any] = {}
        attributes = _without_repeats(self.attributes)
        _ensure_a_resource(attributes)
        for attribute in attributes:
            key = slugify(attribute.name)
            data = {"name": attribute.name, "value_type": attribute.value_type, "resource": attribute.resource}
            if attribute.description:
                data["description"] = attribute.description
            if attribute.value_type in ("integer", "decimal") and not attribute.resource:
                data["min"] = 0
            operations.append({"op": "definition.create", "kind": "attribute", "key": key, "data": data,
                               "reason": "sistema de atributos da campanha"})
            values[key] = attribute.initial_value
        operations.append({"op": "entity.create", "ref": "local_inicial", "kind": "location",
                           "name": self.starting_location, "data": {"description": self.location_description}})
        operations.append({"op": "entity.create", "ref": "protagonista", "kind": self.protagonist.kind or "character",
                           "name": self.protagonist.name, "is_player": True, "location": "local_inicial",
                           "data": {"description": self.protagonist.description}, "attributes": values})
        return operations


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_text).strip("_")
    return slug[:60] or "atributo"


# Nomes típicos de recurso, usados só quando a IA não marcou nenhum (modelos pequenos esquecem).
TYPICAL_RESOURCES = ("vida", "pontos_de_vida", "hp", "saude", "energia", "mana", "vigor", "estamina", "sanidade")


def _without_repeats(attributes: list[SetupAttribute]) -> list[SetupAttribute]:
    """Modelos pequenos às vezes repetem o mesmo atributo; fica só a primeira ocorrência."""
    seen: set[str] = set()
    unique = []
    for attribute in attributes:
        key = slugify(attribute.name)
        if key not in seen:
            seen.add(key)
            unique.append(attribute)
    return unique


def _ensure_a_resource(attributes: list[SetupAttribute]) -> None:
    if any(a.resource for a in attributes):
        return
    for attribute in attributes:
        if slugify(attribute.name) in TYPICAL_RESOURCES and attribute.value_type in ("integer", "decimal"):
            attribute.resource = True
            return
