"""Esquemas das definições criadas pela IA.

Cada tipo tem uma parte OBRIGATÓRIA (validada) e uma parte LIVRE (`extra="allow"`):
a IA pode inventar propriedades novas sem que o motor precise conhecê-las antes.
Tipos desconhecidos também são aceitos (só exigem `name`): o catálogo de tipos é aberto.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError, model_validator

from app.engine.expressions import ExpressionError, analyze
from app.engine.errors import OperationRejected
from app.engine.rules.values import to_decimal

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Number = int | float | str


class OpenDefinition(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: Name
    description: Annotated[str, StringConstraints(max_length=4000)] = ""


class AttributeDefinition(OpenDefinition):
    """Atributo: número inteiro, decimal, faixa nominal ("Rank S") ou conceitual (texto livre)."""

    value_type: Literal["integer", "decimal", "nominal", "conceptual"] = "decimal"
    resource: bool = False  # recurso tem valor atual e máximo (vida, mana...)
    min: Number | None = None
    max: Number | None = None
    scale: list[Name] | None = None  # ordem das faixas nominais, da menor para a maior
    default: Number | None = None

    @model_validator(mode="after")
    def _check(self):
        numeric = self.value_type in ("integer", "decimal")
        if self.resource and not numeric:
            raise ValueError("Recursos precisam ser numéricos (integer ou decimal).")
        if not numeric and (self.min is not None or self.max is not None):
            raise ValueError("min/max só valem para atributos numéricos.")
        if self.scale is not None and self.value_type != "nominal":
            raise ValueError("scale só vale para value_type 'nominal'.")
        if self.min is not None and self.max is not None and to_decimal(self.min) > to_decimal(self.max):
            raise ValueError("min não pode ser maior que max.")
        return self


class SkillCost(BaseModel):
    model_config = ConfigDict(extra="allow")
    resource: Annotated[str, StringConstraints(pattern=r"^[a-z0-9_]{1,100}$")]
    amount: Number  # número ou fórmula


class SkillDefinition(OpenDefinition):
    category: Name | None = None
    rarity: Name | None = None
    max_level: int | None = Field(default=None, ge=1)  # None = sem teto (SPEC 5.2)
    costs: list[SkillCost] = Field(default_factory=list)


class ItemDefinition(OpenDefinition):
    stackable: bool = True


SCHEMAS: dict[str, type[OpenDefinition]] = {
    "attribute": AttributeDefinition,
    "skill": SkillDefinition,
    "item": ItemDefinition,
}
FORMULA_FIELDS = ("formula", "damage", "amount", "modifier", "difficulty")


def validate_definition(kind: str, data: dict[str, Any]) -> dict[str, Any]:
    """Valida e devolve a definição normalizada; fórmulas são conferidas sem calcular."""
    schema = SCHEMAS.get(kind, OpenDefinition)
    try:
        model = schema.model_validate(data)
    except ValidationError as exc:
        first = exc.errors()[0]
        where = ".".join(str(p) for p in first["loc"]) or kind
        raise OperationRejected(f"Definição '{kind}' inválida em '{where}': {first['msg']}") from None
    normalized = model.model_dump(exclude_none=True)
    _check_formulas(normalized)
    return normalized


def _check_formulas(value: Any) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            if key in FORMULA_FIELDS and isinstance(inner, str):
                try:
                    to_decimal(inner)
                except OperationRejected:
                    try:
                        analyze(inner)
                    except ExpressionError as exc:
                        raise OperationRejected(f"Fórmula inválida em '{key}': {exc}") from None
            else:
                _check_formulas(inner)
    elif isinstance(value, list):
        for inner in value:
            _check_formulas(inner)


def attribute_definition(data: dict[str, Any]) -> AttributeDefinition:
    return AttributeDefinition.model_validate(data)
