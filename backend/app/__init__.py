"""AI RPG Engine — pacote principal do backend.

`create_app` é a "fábrica" da aplicação: monta um servidor Flask configurado.
O comando `flask --app app run` encontra essa função automaticamente.
"""

from flask import Flask

from app.config import Settings, load_settings

__version__ = "0.1.0"


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or load_settings()

    flask_app = Flask(__name__)
    flask_app.config.update(
        SECRET_KEY=settings.secret_key,
        TESTING=settings.app_env == "test",
        SETTINGS=settings,
    )

    from app.services.startup import initialize_services

    initialize_services(flask_app, settings)

    from app.api import register_api

    register_api(flask_app)
    return flask_app
