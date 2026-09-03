"""Alembic environment for the Noxyn-Solari schema."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from noxyn_api.config import DEFAULT_DATABASE_URL, sqlalchemy_database_url
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def database_url() -> str:
    cli_url = context.get_x_argument(as_dictionary=True).get("database_url")
    configured_url = config.get_main_option("sqlalchemy.url")
    url = cli_url or os.getenv("DATABASE_URL") or configured_url or DEFAULT_DATABASE_URL
    return sqlalchemy_database_url(url)


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
