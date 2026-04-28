"""
env.py
PRLifts Backend — Alembic environment

Configures Alembic to run migrations against the async SQLAlchemy engine
(asyncpg driver). DATABASE_URL is read from the environment; the alembic.ini
sqlalchemy.url is a fallback for local tooling only.

The database URL is intentionally never logged.
See docs/STANDARDS.md § 2.2 Hard Rules.
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# Load .env.local / .env for local development.
# In Railway, variables are injected directly — load_dotenv is a no-op.
load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata is None — we manage the schema via raw SQL in migration files,
# not via SQLAlchemy ORM metadata. Alembic autogenerate is therefore disabled.
target_metadata = None


def _get_url() -> str:
    """
    Returns the database URL for migrations.

    DATABASE_URL takes precedence over alembic.ini sqlalchemy.url so that
    the same env var used by the application drives migrations in every
    environment. The URL is never logged — it contains credentials.

    Returns:
        asyncpg connection string.
    """
    return os.environ.get(
        "DATABASE_URL",
        config.get_main_option("sqlalchemy.url", ""),
    )


def _do_run_migrations(connection: Connection) -> None:
    """
    Executes pending migrations on the provided synchronous connection.

    Called via connection.run_sync() to bridge async → sync for Alembic.

    Args:
        connection: Synchronous DBAPI connection provided by run_sync.
    """
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    """
    Generates migration SQL without a live database connection.

    Useful for reviewing what will be applied before running it.
    """
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def _run_async_migrations() -> None:
    """
    Applies migrations against a live async database connection.

    Creates a temporary AsyncEngine for the migration run only — separate
    from the application's connection pool managed by app/database.py.
    """
    engine = create_async_engine(_get_url())
    async with engine.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    """Entry point for online (live-database) migration runs."""
    asyncio.run(_run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
