"""Ambiente do Alembic: diz a ele qual banco usar e quais tabelas existem.

O endereço do banco vem de:
1. `sqlalchemy.url` já definido por quem chamou (o próprio programa e os testes); ou
2. `DATABASE_URL` do `.env`, quando o comando `alembic` é usado no terminal.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy.types import TypeDecorator

from app.config import load_settings
from app.persistence.db import create_db_engine
from app.persistence.models import Base

config = context.config

if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def render_item(type_, obj, autogen_context):
    """Escreve tipos próprios (ex.: UTCDateTime) nas migrações como o tipo real do banco.

    Assim os arquivos de migração não dependem do código da aplicação.
    """
    if type_ == "type" and isinstance(obj, TypeDecorator):
        return f"sa.{obj.impl.__class__.__name__}()"
    return False


def _database_url() -> str:
    return config.get_main_option("sqlalchemy.url") or load_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_db_engine(_database_url())
    try:
        with engine.connect() as connection:
            # render_as_batch: o SQLite não altera colunas diretamente; o Alembic recria a tabela.
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                render_as_batch=True,
                compare_type=True,
                render_item=render_item,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
