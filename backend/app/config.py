"""Configuração da aplicação, lida das variáveis de ambiente e do arquivo `.env`.

Prioridade: variável de ambiente real > arquivo `.env` (na raiz do projeto) > valor padrão.
Caminhos relativos (DATA_DIR e banco SQLite) são resolvidos a partir da raiz do projeto,
para o programa funcionar igual não importa de qual pasta ele seja iniciado.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"

VALID_ENVS = ("development", "test", "production")
# Valores de exemplo do .env.example: aceitos no desenvolvimento, recusados em produção.
PLACEHOLDER_VALUES = frozenset({"troque-por-um-texto-aleatorio-longo", "troque-esta-senha"})
DEV_SECRET_KEY = "dev-only-insecure-secret-key"
SQLITE_PREFIX = "sqlite:///"


class ConfigError(Exception):
    """Configuração inválida. A mensagem diz qual variável corrigir."""


@dataclass(frozen=True)
class Settings:
    app_env: str
    data_dir: Path
    database_url: str
    ollama_base_url: str
    openai_compat_base_url: str | None
    ai_spend_limit_per_session: Decimal
    image_provider: str
    # Segredos: repr=False impede que apareçam em logs ou mensagens de erro.
    secret_key: str = field(repr=False)
    admin_password: str | None = field(repr=False)
    openai_compat_api_key: str | None = field(repr=False)
    anthropic_api_key: str | None = field(repr=False)
    image_api_key: str | None = field(repr=False)


def load_settings(
    environ: Mapping[str, str] | None = None,
    env_file: Path | None = DEFAULT_ENV_FILE,
) -> Settings:
    """Monta as configurações. `environ` e `env_file` existem para os testes."""
    values: dict[str, str] = {}
    if env_file is not None and env_file.is_file():
        values.update({k: v for k, v in dotenv_values(env_file).items() if v is not None})
    values.update(os.environ if environ is None else environ)

    def get(key: str, default: str | None = None) -> str | None:
        value = values.get(key, "").strip()
        return value or default

    app_env = get("APP_ENV", "development")
    if app_env not in VALID_ENVS:
        raise ConfigError(f"APP_ENV={app_env!r} inválido. Use um de: {', '.join(VALID_ENVS)}.")

    data_dir = _resolve_path(get("DATA_DIR", "./data"))
    database_url = _resolve_sqlite_url(
        get("DATABASE_URL") or SQLITE_PREFIX + (data_dir / "rpg.db").as_posix()
    )

    secret_key = get("APP_SECRET_KEY")
    admin_password = get("ADMIN_PASSWORD")
    if app_env == "production":
        _require_real_secret("APP_SECRET_KEY", secret_key)
        _require_real_secret("ADMIN_PASSWORD", admin_password)

    return Settings(
        app_env=app_env,
        data_dir=data_dir,
        database_url=database_url,
        ollama_base_url=get("OLLAMA_BASE_URL", "http://localhost:11434"),
        openai_compat_base_url=get("OPENAI_COMPAT_BASE_URL"),
        ai_spend_limit_per_session=_parse_spend_limit(get("AI_SPEND_LIMIT_PER_SESSION", "0")),
        image_provider=get("IMAGE_PROVIDER", "none"),
        secret_key=secret_key or DEV_SECRET_KEY,
        admin_password=admin_password,
        openai_compat_api_key=get("OPENAI_COMPAT_API_KEY"),
        anthropic_api_key=get("ANTHROPIC_API_KEY"),
        image_api_key=get("IMAGE_API_KEY"),
    )


def _resolve_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def _resolve_sqlite_url(url: str) -> str:
    """Torna absoluto o caminho de um banco SQLite relativo. Outros bancos ficam como estão."""
    if not url.startswith(SQLITE_PREFIX):
        return url
    raw_path = url[len(SQLITE_PREFIX):]
    if raw_path in ("", ":memory:"):
        return url
    return SQLITE_PREFIX + _resolve_path(raw_path).as_posix()


def _parse_spend_limit(raw: str) -> Decimal:
    try:
        limit = Decimal(raw)
    except InvalidOperation:
        raise ConfigError(f"AI_SPEND_LIMIT_PER_SESSION={raw!r} não é um número.") from None
    if not limit.is_finite() or limit < 0:
        raise ConfigError("AI_SPEND_LIMIT_PER_SESSION deve ser um número maior ou igual a 0.")
    return limit


def _require_real_secret(name: str, value: str | None) -> None:
    if not value or value in PLACEHOLDER_VALUES:
        raise ConfigError(f"{name} precisa de um valor próprio em produção (não o do exemplo).")
