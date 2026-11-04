"""Hospedagem com um só processo: o backend serve o frontend compilado quando FRONTEND_DIST é definido."""

import pytest

from app import create_app
from app.config import ConfigError
from tests.conftest import make_settings


@pytest.fixture
def dist(tmp_path):
    folder = tmp_path / "dist"
    (folder / "assets").mkdir(parents=True)
    (folder / "index.html").write_text("<div id=app>pagina</div>", encoding="utf-8")
    (folder / "assets" / "index-abc123.js").write_text("console.log('ok')", encoding="utf-8")
    (tmp_path / "segredo.txt").write_text("não pode sair", encoding="utf-8")
    return folder


@pytest.fixture
def client(tmp_path, migrated_db_template, dist):
    application = create_app(make_settings(tmp_path, migrated_db_template, FRONTEND_DIST=str(dist)))
    yield application.test_client()
    application.extensions["rpg_engine"].db.dispose()


def test_pages_and_assets(client):
    for path in ("/", "/campanhas/abc/jogar", "/configuracoes"):
        response = client.get(path)
        assert response.status_code == 200 and b"pagina" in response.data, path
        assert response.cache_control.max_age == 0
    asset = client.get("/assets/index-abc123.js")
    assert asset.status_code == 200 and b"console.log" in asset.data
    assert asset.cache_control.max_age == 31_536_000


def test_api_keeps_working_and_unknown_api_routes_are_json(client):
    assert client.get("/api/health").get_json()["status"] == "ok"
    missing = client.get("/api/nao-existe")
    assert missing.status_code == 404 and missing.get_json()["error"]["code"] == 404


def test_files_outside_dist_are_never_served(client):
    for path in ("/../segredo.txt", "/%2e%2e/segredo.txt", "/assets/../../segredo.txt"):
        response = client.get(path)
        assert "não pode sair".encode() not in response.data, path


def test_disabled_by_default(tmp_path, migrated_db_template):
    application = create_app(make_settings(tmp_path, migrated_db_template))
    assert application.test_client().get("/").status_code == 404
    application.extensions["rpg_engine"].db.dispose()


def test_missing_build_is_a_clear_config_error(tmp_path, migrated_db_template):
    with pytest.raises(ConfigError, match="npm run build"):
        make_settings(tmp_path, migrated_db_template, FRONTEND_DIST=str(tmp_path / "nao-existe"))
