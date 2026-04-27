"""
main.py
PRLifts Backend

FastAPI application entry point. Initialises Sentry error tracking,
structured JSON logging, correlation ID middleware, and the APScheduler
AsyncIOScheduler on startup. All AI operations and periodic cleanup tasks
route through the scheduler — never in synchronous request handlers.
See docs/ARCHITECTURE.md — Backend Tech Stack.

Run locally:
    uvicorn main:app --reload --env-file .env.local
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.config import get_settings
from app.logging_config import configure_logging
from app.middleware.correlation_id import CorrelationIDMiddleware
from app.routers.health import router as health_router

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _init_sentry(dsn: str, environment: str) -> None:
    """
    Initialises Sentry error tracking with PII disabled.

    No-ops when SENTRY_DSN is empty — Sentry is optional in local development.
    send_default_pii=False is required by docs/STANDARDS.md § 10 Privacy Standards.

    Args:
        dsn: Sentry project DSN. Empty string disables initialisation.
        environment: Deployment environment (development/staging/production).
    """
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        send_default_pii=False,
        integrations=[StarletteIntegration(), FastApiIntegration()],
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages application startup and shutdown.

    Startup: configures structured logging, initialises Sentry, starts APScheduler.
    Shutdown: stops APScheduler cleanly.

    APScheduler must start here — not via the deprecated @app.on_event decorator.
    See docs/STANDARDS.md § 7.6 APScheduler Standard.

    Args:
        app: The FastAPI application instance.

    Yields:
        Control to the running application.
    """
    settings = get_settings()
    configure_logging(settings.log_level)
    _init_sentry(settings.sentry_dsn, settings.environment)

    scheduler.start()
    logger.info(
        "Application started",
        extra={
            "environment": settings.environment,
            "version": settings.app_version,
        },
    )

    yield

    scheduler.shutdown()
    logger.info("Application stopped")


def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application.

    Registers the correlation ID middleware and all routers.
    The lifespan context manager handles all startup/shutdown side effects.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="PRLifts API",
        lifespan=lifespan,
    )
    app.add_middleware(CorrelationIDMiddleware)
    app.include_router(health_router)
    return app


app = create_app()
