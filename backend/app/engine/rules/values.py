"""Números e valores de atributos (Decimal em texto: sem teto e sem perda de precisão)."""

from __future__ import annotations

import decimal
from decimal import Decimal
from typing import TYPE_CHECKING

from app.engine.errors import OperationRejected

if TYPE_CHECKING:
    from app.engine.rules.definitions import AttributeDefinition

MAX_NUMBER_TEXT = 200


def to_decimal(raw: object) -> Decimal:
    if isinstance(raw, bool):
        raise OperationRejected("Esperava um número, não verdadeiro/falso.")
    if isinstance(raw, Decimal):
        value = raw
    else:
        text = str(raw).strip()
        if not text or len(text) > MAX_NUMBER_TEXT:
            raise OperationRejected(f"'{raw}' não é um número válido.")
        try:
            value = Decimal(text)
        except decimal.InvalidOperation:
            raise OperationRejected(f"'{raw}' não é um número válido.") from None
    if not value.is_finite():
        raise OperationRejected("Números precisam ser finitos.")
    return value


def number_text(value: Decimal) -> str:
    """Texto canônico: '10' em vez de '10.000', '1.5E+40' para números enormes."""
    if value == value.to_integral_value():
        quantized = value.quantize(Decimal(1)) if abs(value.adjusted()) < 30 else value.normalize()
        return str(quantized) if quantized != 0 else "0"
    return str(value.normalize())


def normalize_value(definition: AttributeDefinition, raw: object) -> str:
    """Converte para o formato do atributo e confere os limites declarados."""
    if definition.value_type == "conceptual":
        return _text(raw)
    if definition.value_type == "nominal":
        text = _text(raw)
        if definition.scale is not None and text not in definition.scale:
            raise OperationRejected(f"'{text}' não está na escala de {definition.name}: {', '.join(definition.scale)}.")
        return text
    value = to_decimal(raw)
    if definition.value_type == "integer" and value != value.to_integral_value():
        raise OperationRejected(f"{definition.name} só aceita números inteiros.")
    check_bounds(definition, value)
    return number_text(value)


def check_bounds(definition: AttributeDefinition, value: Decimal) -> None:
    if definition.min is not None and value < to_decimal(definition.min):
        raise OperationRejected(f"{definition.name} não pode ficar abaixo de {definition.min}.")
    if definition.max is not None and value > to_decimal(definition.max):
        raise OperationRejected(f"{definition.name} não pode passar de {definition.max}.")


def _text(raw: object) -> str:
    text = str(raw).strip()
    if not text or len(text) > 500:
        raise OperationRejected("Valor de texto vazio ou longo demais.")
    return text
