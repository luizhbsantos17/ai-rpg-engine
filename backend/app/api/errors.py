"""Erros da API sempre respondem em JSON, no formato {"error": {"code", "name", "message"}}.

Erros inesperados nunca expõem detalhes internos na resposta; o detalhe vai para o log.
"""

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException


def _error_response(code: int, name: str, message: str):
    return jsonify(error={"code": code, "name": name, "message": message}), code


def register_error_handlers(flask_app: Flask, api_prefix: str) -> None:
    @flask_app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        if not request.path.startswith(api_prefix + "/"):
            return error
        return _error_response(error.code, error.name, error.description)

    @flask_app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        flask_app.logger.exception("Erro inesperado em %s %s", request.method, request.path)
        return _error_response(500, "Internal Server Error", "Erro interno no servidor. Detalhes no log.")
