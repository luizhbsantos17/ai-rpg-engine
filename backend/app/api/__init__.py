"""Rotas HTTP do backend. Todas ficam sob o prefixo /api."""

from flask import Flask

from app.api import health
from app.api.errors import register_error_handlers

API_PREFIX = "/api"


def register_api(flask_app: Flask) -> None:
    flask_app.register_blueprint(health.bp, url_prefix=API_PREFIX)
    register_error_handlers(flask_app, API_PREFIX)
