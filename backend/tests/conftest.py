"""Peças compartilhadas pelos testes (fixtures do pytest).

Cada teste recebe sua própria pasta de dados temporária e um banco SQLite próprio,
copiado de um modelo já migrado (mais rápido que migrar de novo em cada teste).
"""

import shutil

import pytest

from app import create_app
from app.config import load_settings
from app.persistence.db import Database
from app.persistence.migrations import upgrade_to_head


@pytest.fixture(scope="session")
def migrated_db_template(tmp_path_factory):
    path = tmp_path_factory.mktemp("template") / "rpg.db"
    upgrade_to_head("sqlite:///" + path.as_posix())
    return path


def make_settings(tmp_path, template, **extra):
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    shutil.copy(template, data_dir / "rpg.db")
    environ = {"APP_ENV": "test", "DATA_DIR": str(data_dir), "AI_PROVIDER": "fake", "AI_MODEL": "fake-model",
               "AI_MECHANICS": "false", **extra}
    # env_file=None: os testes nunca leem o .env real do usuário.
    return load_settings(environ=environ, env_file=None)


@pytest.fixture
def settings(tmp_path, migrated_db_template):
    """Fluxo só de narração (Etapa 1). Os testes do motor usam `mechanics_settings`."""
    return make_settings(tmp_path, migrated_db_template)


@pytest.fixture
def mechanics_settings(tmp_path, migrated_db_template):
    return make_settings(tmp_path, migrated_db_template, AI_MECHANICS="true")


@pytest.fixture
def db(settings):
    database = Database(settings.database_url)
    yield database
    database.dispose()


@pytest.fixture
def flask_app(settings):
    application = create_app(settings)
    yield application
    application.extensions["rpg_engine"].db.dispose()


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


@pytest.fixture
def services(flask_app):
    return flask_app.extensions["rpg_engine"]


@pytest.fixture
def fake_ai(services):
    """O FakeProvider da aplicação de teste; use fake_ai.queue("texto") para roteirizar."""
    return services.provider
