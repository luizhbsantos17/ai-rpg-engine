"""Aplica as migrações do Alembic pelo próprio programa.

Ao iniciar, o backend leva o banco para a versão mais recente do esquema. Assim o
usuário não precisa rodar comandos de banco à mão (instalação simples, RNF-07).
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

BACKEND_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"


def alembic_config(database_url: str) -> Config:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    # "%" tem significado especial no arquivo .ini; precisa ser duplicado.
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    # Avisa o env.py para não reconfigurar os logs da aplicação.
    config.attributes["configure_logger"] = False
    return config


def upgrade_to_head(database_url: str) -> None:
    command.upgrade(alembic_config(database_url), "head")
