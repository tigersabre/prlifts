"""
db.py
PRLifts Backend

asyncpg connection pool factory. Strips the SQLAlchemy-style
`postgresql+asyncpg://` prefix that Alembic uses so the raw DSN is
compatible with asyncpg.create_pool (which expects `postgresql://`).

See docs/ARCHITECTURE.md Decision 96 — direct asyncpg pool.
"""

import asyncpg


async def create_pool(database_url: str, max_size: int = 10) -> asyncpg.Pool:
    """
    Creates an asyncpg connection pool from database_url.

    Strips the `postgresql+asyncpg://` prefix used by Alembic/SQLAlchemy so
    that asyncpg receives the plain `postgresql://` DSN it expects.

    Args:
        database_url: Full PostgreSQL connection string from DATABASE_URL env var.
        max_size: Maximum number of connections in the pool.

    Returns:
        Initialised asyncpg.Pool.
    """
    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    pool: asyncpg.Pool = await asyncpg.create_pool(dsn, max_size=max_size)
    return pool
