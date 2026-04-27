"""
conftest.py
PRLifts Backend Tests

Shared pytest fixtures and environment bootstrap. Environment variables
must be set before any app module is imported because Settings reads
os.environ at construction time. The os.environ assignments at the top of
this file run before pytest collects or imports test modules.
"""

import os
from collections.abc import Generator

# Must precede all app imports — Settings reads these at construction time.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("APP_VERSION", "0.1.0")
# Fake DATABASE_URL used for unit tests — no real connection is made at engine
# creation time (SQLAlchemy is lazy). Pool sizes are small to keep tests fast.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://fake:fake@localhost:5432/fake_test"
)
os.environ.setdefault("DB_POOL_SIZE", "2")
os.environ.setdefault("DB_MAX_OVERFLOW", "1")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """
    Provides a synchronous TestClient with the full app lifespan active.

    The lifespan context manager (logging, Sentry, APScheduler) runs for
    the duration of the test module, then shuts down cleanly.

    Yields:
        TestClient with the app lifespan context active.
    """
    with TestClient(app) as test_client:
        yield test_client
