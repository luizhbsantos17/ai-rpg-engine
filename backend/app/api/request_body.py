"""Leitura e validação do corpo JSON das requisições."""

from __future__ import annotations

from typing import TypeVar

from flask import request
from pydantic import BaseModel

from app.services.errors import InvalidInputError

ModelT = TypeVar("ModelT", bound=BaseModel)


def parse_body(schema: type[ModelT]) -> ModelT:
    """Valida o JSON recebido; erros de formato viram ValidationError (respondido como 400)."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise InvalidInputError("O corpo da requisição precisa ser um objeto JSON.")
    return schema.model_validate(data)
