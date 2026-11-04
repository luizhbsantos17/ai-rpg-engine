"""Peças compartilhadas pelos testes (fixtures do pytest)."""

import pytest

from app import create_app
from app.config import load_settings


@pytest.fixture
def settings(tmp_path):
    # env_file=None: os testes nunca leem o .env real do usuário.
    return load_settings(
        environ={"APP_ENV": "test", "DATA_DIR": str(tmp_path / "data")},
        env_file=None,
    )


@pytest.fixture
def flask_app(settings):
    return create_app(settings)


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()
