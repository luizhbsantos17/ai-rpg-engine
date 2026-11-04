"""Preparação feita uma vez quando o backend inicia."""

from __future__ import annotations

from flask import Flask, current_app

from app.auth.local_user import ensure_local_user
from app.config import Settings
from app.persistence.db import Database
from app.persistence.migrations import upgrade_to_head

EXTENSION_KEY = "rpg_engine"


class Services:
    """Objetos compartilhados pela aplicação inteira (guardados em `flask_app.extensions`)."""

    def __init__(self, settings: Settings, db: Database, local_user_id: str):
        self.settings = settings
        self.db = db
        self.local_user_id = local_user_id


def initialize_services(flask_app: Flask, settings: Settings) -> Services:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    upgrade_to_head(settings.database_url)

    db = Database(settings.database_url)
    with db.transaction() as session:
        local_user_id = ensure_local_user(session).id

    services = Services(settings, db, local_user_id)
    flask_app.extensions[EXTENSION_KEY] = services
    return services


def get_services() -> Services:
    return current_app.extensions[EXTENSION_KEY]
