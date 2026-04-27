"""
test_database.py
PRLifts Backend Tests

Tests for app/database.py: engine creation, pool initialisation, session
dependency, rollback-on-exception, and credential safety (connection string
must never appear in log output).

The integration test at the bottom requires a real PostgreSQL instance and is
skipped automatically when ENVIRONMENT=test (the default for the unit test run).
To run it locally: set ENVIRONMENT=development and provide a real DATABASE_URL.
"""

import logging
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

# ── Engine creation ────────────────────────────────────────────────────────────


def test_build_engine_returns_async_engine() -> None:
    # Arrange
    from app.database import build_engine

    # Act
    engine = build_engine(
        "postgresql+asyncpg://fake:fake@localhost:5432/fake_test", 2, 1
    )

    # Assert
    assert isinstance(engine, AsyncEngine)


def test_build_engine_applies_pool_configuration() -> None:
    # Arrange
    from app.database import build_engine

    # Act
    engine = build_engine(
        "postgresql+asyncpg://fake:fake@localhost:5432/fake_test",
        pool_size=3,
        max_overflow=2,
    )

    # Assert — SQLAlchemy exposes pool config on the underlying sync engine
    pool = engine.sync_engine.pool
    assert pool.size() == 3  # type: ignore[attr-defined]


# ── Pool initialisation ────────────────────────────────────────────────────────


async def test_init_db_sets_engine_and_session_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    import app.database as db_module

    mock_engine = AsyncMock(spec=AsyncEngine)
    mock_factory = MagicMock()

    monkeypatch.setattr(db_module, "_engine", None)
    monkeypatch.setattr(db_module, "_session_factory", None)

    # Act
    with (
        patch("app.database.build_engine", return_value=mock_engine),
        patch("app.database.async_sessionmaker", return_value=mock_factory),
    ):
        await db_module.init_db()

    # Assert
    assert db_module._engine is mock_engine
    assert db_module._session_factory is mock_factory


async def test_init_db_logs_pool_size_not_credentials(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    # Arrange
    import app.database as db_module

    monkeypatch.setattr(db_module, "_engine", None)
    monkeypatch.setattr(db_module, "_session_factory", None)

    # Act
    with (
        patch("app.database.build_engine", return_value=AsyncMock(spec=AsyncEngine)),
        patch("app.database.async_sessionmaker", return_value=MagicMock()),
        caplog.at_level(logging.INFO, logger="app.database"),
    ):
        await db_module.init_db()

    # Assert — pool size is logged, credentials are not
    assert any("pool" in r.message.lower() for r in caplog.records)
    database_url = os.environ.get("DATABASE_URL", "")
    for record in caplog.records:
        assert database_url not in record.getMessage()


# ── Pool shutdown ──────────────────────────────────────────────────────────────


async def test_close_db_disposes_engine_and_clears_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    import app.database as db_module

    mock_engine = AsyncMock(spec=AsyncEngine)
    mock_factory = MagicMock()
    monkeypatch.setattr(db_module, "_engine", mock_engine)
    monkeypatch.setattr(db_module, "_session_factory", mock_factory)

    # Act
    await db_module.close_db()

    # Assert
    mock_engine.dispose.assert_awaited_once()
    assert db_module._engine is None
    assert db_module._session_factory is None


async def test_close_db_is_noop_when_engine_is_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    import app.database as db_module

    monkeypatch.setattr(db_module, "_engine", None)

    # Act + Assert — no exception raised
    await db_module.close_db()


# ── Session dependency ─────────────────────────────────────────────────────────


async def test_get_db_raises_when_pool_not_initialised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    import app.database as db_module

    monkeypatch.setattr(db_module, "_session_factory", None)

    # Act + Assert
    with pytest.raises(RuntimeError, match="not initialised"):
        async for _ in db_module.get_db():
            pass


async def test_get_db_yields_session_to_caller(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    import app.database as db_module

    mock_session = AsyncMock(spec=AsyncSession)
    mock_factory = _make_session_factory(mock_session)
    monkeypatch.setattr(db_module, "_session_factory", mock_factory)

    # Act
    yielded: list[AsyncSession] = []
    async for session in db_module.get_db():
        yielded.append(session)

    # Assert
    assert len(yielded) == 1
    assert yielded[0] is mock_session


async def test_get_db_rolls_back_session_when_handler_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    import app.database as db_module

    mock_session = AsyncMock(spec=AsyncSession)
    mock_factory = _make_session_factory(mock_session)
    monkeypatch.setattr(db_module, "_session_factory", mock_factory)

    gen = db_module.get_db()

    # Advance the generator to the yield point (FastAPI does this on request entry)
    await gen.__anext__()

    # Act — simulate FastAPI injecting the route exception via athrow(),
    # which is how FastAPI's dependency system propagates handler exceptions.
    # A plain `async for` body-raise does NOT throw back into the generator.
    with pytest.raises(ValueError, match="deliberate"):
        await gen.athrow(ValueError("deliberate test error"))

    # Assert — session was rolled back before the exception propagated
    mock_session.rollback.assert_awaited_once()


# ── Integration test ───────────────────────────────────────────────────────────


@pytest.mark.skipif(
    os.environ.get("ENVIRONMENT") == "test",
    reason=(
        "Integration test requires a real PostgreSQL instance. "
        "Run locally with ENVIRONMENT=development and a valid DATABASE_URL."
    ),
)
async def test_database_simple_query_executes_against_real_database() -> None:
    # Arrange — build a real engine using the configured DATABASE_URL
    from sqlalchemy import text

    import app.database as db_module
    from app.config import get_settings

    settings = get_settings()
    engine = db_module.build_engine(
        settings.database_url, settings.db_pool_size, settings.db_max_overflow
    )

    # Act — execute a trivial query to confirm the connection is live
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        row = result.fetchone()

    await engine.dispose()

    # Assert
    assert row is not None
    assert row[0] == 1


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_session_factory(mock_session: AsyncMock) -> MagicMock:
    """
    Builds a mock async_sessionmaker whose context manager yields mock_session.

    The factory call returns a context manager that enters to mock_session
    and exits cleanly, mirroring how async_sessionmaker behaves.
    """
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=False)

    factory = MagicMock()
    factory.return_value = ctx
    return factory
