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
from datetime import UTC, datetime

import sentry_sdk
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.config import get_settings
from app.db import create_pool
from app.logging_config import configure_logging
from app.middleware.correlation_id import CorrelationIDMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.repositories.asyncpg_exercise_repository import AsyncpgExerciseRepository
from app.repositories.asyncpg_job_repository import (
    AsyncpgAIRequestLogRepository,
    AsyncpgJobRepository,
    AsyncpgPromptTemplateRepository,
)
from app.repositories.asyncpg_personal_record_repository import (
    AsyncpgPersonalRecordRepository,
)
from app.repositories.asyncpg_stats_repository import AsyncpgStatsRepository
from app.repositories.asyncpg_user_repository import AsyncpgUserRepository
from app.repositories.asyncpg_workout_exercise_repository import (
    AsyncpgWorkoutExerciseRepository,
)
from app.repositories.asyncpg_workout_repository import AsyncpgWorkoutRepository
from app.repositories.asyncpg_workout_set_repository import AsyncpgWorkoutSetRepository
from app.repositories.exercise_repository import get_exercise_repository
from app.repositories.job_repository import (
    get_ai_request_log_repository,
    get_job_repository,
    get_prompt_template_repository,
)
from app.repositories.personal_record_repository import get_personal_record_repository
from app.repositories.stats_repository import get_stats_repository
from app.repositories.user_repository import get_user_repository
from app.repositories.workout_exercise_repository import get_workout_exercise_repository
from app.repositories.workout_repository import get_workout_repository
from app.repositories.workout_set_repository import get_workout_set_repository
from app.routers.account import router as account_router
from app.routers.exercises import router as exercises_router
from app.routers.health import router as health_router
from app.routers.jobs import router as jobs_router
from app.routers.stats import router as stats_router
from app.routers.users import router as users_router
from app.routers.workout_exercises import router as workout_exercises_router
from app.routers.workout_sets import router as workout_sets_router
from app.routers.workouts import router as workouts_router

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

    redis_client = None
    if settings.redis_url:
        from redis.asyncio import Redis

        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    app.state.redis = redis_client

    pool = None
    if settings.database_url:
        pool = await create_pool(settings.database_url, settings.pool_max_size)

        app.dependency_overrides[get_user_repository] = lambda: AsyncpgUserRepository(
            pool
        )
        app.dependency_overrides[get_workout_repository] = lambda: (
            AsyncpgWorkoutRepository(pool)
        )
        app.dependency_overrides[get_workout_exercise_repository] = lambda: (
            AsyncpgWorkoutExerciseRepository(pool)
        )
        app.dependency_overrides[get_workout_set_repository] = lambda: (
            AsyncpgWorkoutSetRepository(pool)
        )
        app.dependency_overrides[get_personal_record_repository] = lambda: (
            AsyncpgPersonalRecordRepository(pool)
        )
        app.dependency_overrides[get_exercise_repository] = lambda: (
            AsyncpgExerciseRepository(pool)
        )
        app.dependency_overrides[get_stats_repository] = lambda: AsyncpgStatsRepository(
            pool
        )
        app.dependency_overrides[get_job_repository] = lambda: AsyncpgJobRepository(
            pool
        )
        app.dependency_overrides[get_prompt_template_repository] = lambda: (
            AsyncpgPromptTemplateRepository(pool)
        )
        app.dependency_overrides[get_ai_request_log_repository] = lambda: (
            AsyncpgAIRequestLogRepository(pool)
        )

        job_repo = AsyncpgJobRepository(pool)

        async def _cleanup_expired_jobs() -> None:
            count = await job_repo.expire_stale(datetime.now(UTC))
            if count:
                logger.info("Expired stale jobs", extra={"count": count})

        scheduler.add_job(
            _cleanup_expired_jobs,
            "interval",
            seconds=60,
            id="cleanup_expired_jobs",
        )

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
    if pool is not None:
        await pool.close()
    if app.state.redis is not None:
        await app.state.redis.aclose()
    logger.info("Application stopped")


async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Returns our standard ErrorResponse format for HTTPExceptions.

    When exc.detail is already a dict (our ErrorResponse shape), it is returned
    directly — no "detail" wrapper. Other details (strings, lists) keep the
    default FastAPI "detail" wrapper so Starlette built-in 404/405/422 errors
    are still well-formed.

    See docs/ERROR_CATALOG.md for the canonical error response format.
    """
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
            headers=exc.headers,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application.

    Registers the correlation ID middleware, the custom error handler, and all
    routers. The lifespan context manager handles all startup/shutdown side effects.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="PRLifts API",
        lifespan=lifespan,
    )
    # Middleware registration order: last-added runs first (outermost).
    # CorrelationIDMiddleware must run before RateLimitMiddleware so that
    # request.state.correlation_id is populated for the 429 error body.
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(CorrelationIDMiddleware)
    app.add_exception_handler(HTTPException, _http_exception_handler)  # type: ignore[arg-type]
    app.include_router(health_router)
    app.include_router(users_router, prefix="/v1")
    app.include_router(workouts_router, prefix="/v1")
    app.include_router(workout_exercises_router, prefix="/v1")
    app.include_router(workout_sets_router, prefix="/v1")
    app.include_router(exercises_router, prefix="/v1")
    app.include_router(jobs_router, prefix="/v1")
    app.include_router(stats_router, prefix="/v1")
    app.include_router(account_router, prefix="/v1")
    return app


app = create_app()
