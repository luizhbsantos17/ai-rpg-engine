from decimal import Decimal

import pytest

from app.config import PROJECT_ROOT, ConfigError, load_settings


def load(environ=None, env_file=None):
    return load_settings(environ=environ or {}, env_file=env_file)


def test_defaults_work_without_env_file():
    s = load()
    assert s.app_env == "development"
    assert s.data_dir == (PROJECT_ROOT / "data").resolve()
    assert s.database_url == "sqlite:///" + (PROJECT_ROOT / "data" / "rpg.db").resolve().as_posix()
    assert s.ollama_base_url == "http://localhost:11434"
    assert s.ai_spend_limit_per_session == Decimal("0")
    assert s.image_provider == "none"
    assert s.anthropic_api_key is None


def test_relative_paths_do_not_depend_on_current_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    s = load({"DATA_DIR": "./data", "DATABASE_URL": "sqlite:///./data/rpg.db"})
    assert s.data_dir == (PROJECT_ROOT / "data").resolve()
    assert s.database_url.endswith((PROJECT_ROOT / "data" / "rpg.db").resolve().as_posix())


def test_non_sqlite_and_memory_urls_are_kept():
    assert load({"DATABASE_URL": "postgresql://u@h/db"}).database_url == "postgresql://u@h/db"
    assert load({"DATABASE_URL": "sqlite:///:memory:"}).database_url == "sqlite:///:memory:"


def test_env_file_is_read_and_real_environment_wins(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=test\nOLLAMA_BASE_URL=http://arquivo:1\n", encoding="utf-8")
    s = load({"OLLAMA_BASE_URL": "http://ambiente:2"}, env_file=env_file)
    assert s.app_env == "test"
    assert s.ollama_base_url == "http://ambiente:2"


def test_empty_values_count_as_not_set():
    s = load({"OPENAI_COMPAT_API_KEY": "", "IMAGE_PROVIDER": "  "})
    assert s.openai_compat_api_key is None
    assert s.image_provider == "none"


def test_env_example_file_is_valid():
    s = load(env_file=PROJECT_ROOT / ".env.example")
    assert s.app_env == "development"


def test_invalid_app_env_is_rejected():
    with pytest.raises(ConfigError, match="APP_ENV"):
        load({"APP_ENV": "producao"})


@pytest.mark.parametrize("raw", ["abc", "-1", "NaN", "Infinity"])
def test_invalid_spend_limit_is_rejected(raw):
    with pytest.raises(ConfigError, match="AI_SPEND_LIMIT_PER_SESSION"):
        load({"AI_SPEND_LIMIT_PER_SESSION": raw})


def test_spend_limit_accepts_decimals():
    assert load({"AI_SPEND_LIMIT_PER_SESSION": "2.50"}).ai_spend_limit_per_session == Decimal("2.50")


@pytest.mark.parametrize(
    "environ",
    [
        {},
        {"APP_SECRET_KEY": "troque-por-um-texto-aleatorio-longo", "ADMIN_PASSWORD": "senha-real"},
        {"APP_SECRET_KEY": "chave-real", "ADMIN_PASSWORD": "troque-esta-senha"},
    ],
)
def test_production_requires_real_secrets(environ):
    with pytest.raises(ConfigError, match="produção"):
        load({"APP_ENV": "production", **environ})


def test_production_accepts_real_secrets():
    s = load({"APP_ENV": "production", "APP_SECRET_KEY": "chave-real", "ADMIN_PASSWORD": "senha-real"})
    assert s.secret_key == "chave-real"


def test_secrets_never_appear_in_repr():
    s = load({
        "APP_SECRET_KEY": "SEGREDO-1",
        "ADMIN_PASSWORD": "SEGREDO-2",
        "OPENAI_COMPAT_API_KEY": "SEGREDO-3",
        "ANTHROPIC_API_KEY": "SEGREDO-4",
        "IMAGE_API_KEY": "SEGREDO-5",
    })
    assert "SEGREDO" not in repr(s)
