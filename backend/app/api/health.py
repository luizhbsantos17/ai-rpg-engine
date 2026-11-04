"""GET /api/health — confirma que o servidor está no ar."""

from flask import Blueprint, current_app

from app import __version__

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    settings = current_app.config["SETTINGS"]
    return {"status": "ok", "version": __version__, "env": settings.app_env}
