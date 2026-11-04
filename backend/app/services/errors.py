"""Erros de regra de negócio, convertidos em respostas HTTP pela API."""

from __future__ import annotations


class ServiceError(Exception):
    http_status = 400
    code = "invalid_request"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(ServiceError):
    http_status = 404
    code = "not_found"


class ConflictError(ServiceError):
    """O pedido não combina com o estado atual (ex.: turno já em andamento)."""

    http_status = 409
    code = "conflict"


class UnavailableError(ServiceError):
    """Um serviço necessário (ex.: a IA) não respondeu; tentar de novo pode funcionar."""

    http_status = 503
    code = "unavailable"


class InvalidInputError(ServiceError):
    http_status = 400
    code = "invalid_input"
