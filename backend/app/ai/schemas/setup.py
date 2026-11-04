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


class SetupCompanion(BaseModel):
    """Integrante de uma turma/grupo: cada um com identidade própria (SPEC 4.3)."""

    model_config = ConfigDict(extra="ignore")
    name: str = Field(min_length=1, max_length=200)
    kind: str = Field(default="character", max_length=40)
    description: str = Field(default="", max_length=1000)
    personality: str = Field(default="", max_length=500)
    goal: str = Field(default="", max_length=500)
    bond: str = Field(default="", max_length=60, description="laço com o protagonista: amigo, rival, desconhecido...")
    attributes: dict[str, int | float | str] = Field(default_factory=dict, description="nome do atributo -> valor")


class SetupDeathRule(BaseModel):
    model_config = ConfigDict(extra="ignore")
    mode: Literal["permanent", "unconscious", "resurrection", "reincarnation", "narrative"] = "narrative"
    description: str = Field(default="", max_length=1000)
    revive_after: str | None = Field(default=None, max_length=30, description='ex.: "8h", "3d"')


class CampaignSetup(BaseModel):
    model_config = ConfigDict(extra="ignore")
    attributes: list[SetupAttribute] = Field(min_length=1, max_length=12)
    protagonist: SetupProtagonist
    starting_location: str = Field(min_length=1, max_length=200)
    location_description: str = Field(default="", max_length=2000)
    world_facts: list[str] = Field(default_factory=list, max_length=8,
                                   description="fatos importantes do mundo, incluindo como funciona a morte")
    companions: list[SetupCompanion] = Field(default_factory=list, max_length=8)
    death_rule: SetupDeathRule | None = None

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
        operations += self._death_rule_operation(attributes)
        facts = [fact.strip() for fact in self.world_facts if fact.strip()]
        for index, fact in enumerate(facts, start=1):
            operations.append({"op": "canon.assert", "key": f"mundo_{index}", "subject": "mundo",
                               "statement": fact[:2000], "reason": "fato inicial do universo"})
        operations.append({"op": "entity.create", "ref": "protagonista", "kind": self.protagonist.kind or "character",
                           "name": self.protagonist.name, "is_player": True, "location": "local_inicial",
                           "data": {"description": self.protagonist.description}, "attributes": values})
        operations += self._companion_operations(set(values))
        return operations

    def _death_rule_operation(self, attributes: list[SetupAttribute]) -> list[dict[str, Any]]:
        """A regra de morte vale para o primeiro recurso (ex.: Vida). Sem recurso, não há regra automática."""
        vital = next((slugify(a.name) for a in attributes if a.resource), None)
        if self.death_rule is None or vital is None:
            return []
        rule = self.death_rule
        mode = rule.mode
        if mode in ("unconscious", "resurrection") and not rule.revive_after:
            mode = "narrative"  # sem tempo de volta, o motor não inventa um: a narração decide
        data: dict[str, Any] = {"name": "Regra de morte", "mode": mode, "vital_resource": vital,
                                "description": rule.description}
        if mode in ("unconscious", "resurrection"):
            data["revive_after"] = rule.revive_after
        return [{"op": "definition.create", "kind": "death_rule", "key": "regra_de_morte", "data": data,
                 "reason": "como a morte funciona neste universo"}]

    def _companion_operations(self, attribute_keys: set[str]) -> list[dict[str, Any]]:
        operations: list[dict[str, Any]] = []
        for index, companion in enumerate(self.companions, start=1):
            ref = f"companheiro_{index}"
            # Só atributos que existem no sistema da campanha; nomes desconhecidos são ignorados.
            attributes = {slugify(name): value for name, value in companion.attributes.items()
                          if slugify(name) in attribute_keys}
            data = {k: v for k, v in {"description": companion.description, "personality": companion.personality,
                                      "goal": companion.goal}.items() if v}
            operations.append({"op": "entity.create", "ref": ref, "kind": companion.kind or "character",
                               "name": companion.name, "location": "local_inicial", "data": data,
                               "attributes": attributes})
            if companion.bond.strip():
                operations.append({"op": "relationship.change", "source": ref, "target": "protagonista",
                                   "add_labels": [companion.bond.strip()], "cause": "como tudo começou"})
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
