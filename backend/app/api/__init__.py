"""Rotas HTTP do backend. Todas ficam sob o prefixo /api."""

from flask import Flask

from app.api import campaigns, health, turns
from app.api.errors import register_error_handlers

API_PREFIX = "/api"


def register_api(flask_app: Flask) -> None:
    for module in (health, campaigns, turns):
        flask_app.register_blueprint(module.bp, url_prefix=API_PREFIX)
    register_error_handlers(flask_app, API_PREFIX)
