"""Erros da API sempre respondem em JSON, no formato {"error": {"code", "name", "message"}}.

Erros inesperados nunca expõem detalhes internos na resposta; o detalhe vai para o log.
"""

from flask import Flask, jsonify, request
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from app.services.errors import ServiceError


def _error_response(code: int, name: str, message: str, details=None):
    error = {"code": code, "name": name, "message": message}
    if details:
        error["details"] = details
    return jsonify(error=error), code


def register_error_handlers(flask_app: Flask, api_prefix: str) -> None:
    @flask_app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        if not request.path.startswith(api_prefix + "/"):
            return error
        return _error_response(error.code, error.name, error.description)

    @flask_app.errorhandler(ServiceError)
    def handle_service_error(error: ServiceError):
        return _error_response(error.http_status, error.code, error.message)

    @flask_app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        details = [
            {"field": ".".join(str(p) for p in e["loc"]), "problem": e["msg"]} for e in error.errors()
        ]
        return _error_response(400, "invalid_input", "Dados inválidos.", details)

    @flask_app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        flask_app.logger.exception("Erro inesperado em %s %s", request.method, request.path)
        return _error_response(500, "Internal Server Error", "Erro interno no servidor. Detalhes no log.")
