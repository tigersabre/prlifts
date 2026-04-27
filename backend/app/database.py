"""
database.py
PRLifts Backend

SQLAlchemy async engine and session factory for Supabase PostgreSQL.
The engine is created once on startup and disposed on shutdown via
FastAPI's lifespan context manager. Every route that needs the database
receives a session through the get_db() FastAPI dependency.

Security: DATABASE_URL contains credentials and is never logged at any level.
See docs/STANDARDS.md § 2.2 Hard Rules — Never in Code.
See docs/ARCHITECTURE.md — Backend Tech Stack.
"""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def build_engine(database_url: str, pool_size: int, max_overflow: int) -> AsyncEngine:
    """
    Creates a SQLAlchemy async engine for PostgreSQL via asyncpg.

    database_url is accepted as a parameter rather than read from settings
    inside this function so that tests can inject a value without creating a
    real connection. pool_pre_ping=True recycles stale connections after a
    Supabase-side timeout or network event.

    The database_url is intentionally not logged — it contains credentials.
    See docs/STANDARDS.md § 2.2 Hard Rules.

    Args:
        database_url: asyncpg connection string. Never logged at any level.
        pool_size: Minimum open connections kept in the pool.
        max_overflow: Additional connections allowed above pool_size.

    Returns:
        Configured AsyncEngine instance (no connection is made at this point).
    """
    return create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
    )


async def init_db() -> None:
    """
    Creates the async engine and session factory from application settings.

    Called once from the FastAPI lifespan on startup. Only pool sizing is
    logged — the connection string and credentials are never emitted.
    """
    global _engine, _session_factory
    settings = get_settings()

    _engine = build_engine(
        settings.database_url,
        settings.db_pool_size,
        settings.db_max_overflow,
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)

    logger.info(
        "Database connection pool initialised",
        extra={
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
        },
    )


async def close_db() -> None:
    """
    Disposes the async engine and releases all pooled connections.

    Called from the FastAPI lifespan on shutdown. Clears both the engine and
    the session factory so any post-shutdown call to get_db() fails fast.
    Safe to call even if init_db() was never reached.
    """
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database connection pool closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an AsyncSession scoped to one request.

    If the handler raises without committing, the session is explicitly
    rolled back before closing. Callers must commit explicitly when writes
    should be persisted — this function does not auto-commit.

    Yields:
        AsyncSession for the current request.

    Raises:
        RuntimeError: If init_db() was not called before the first request.
    """
    if _session_factory is None:
        raise RuntimeError(
            "Database pool not initialised. "
            "Ensure init_db() is called in the FastAPI lifespan."
        )

    async with _session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
