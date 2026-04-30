"""
rate_limit.py
PRLifts Backend

Rate limiting middleware using Redis fixed-window counters (60-second windows).

Three tiers, per docs/ARCHITECTURE.md — Security Standards:
  AI endpoints (/v1/jobs):       10 requests/min per authenticated user
  Auth endpoints (/v1/auth):      5 requests/min per IP
  General endpoints (/v1/...):  100 requests/min per authenticated user

Rate limit key format: {identifier}:{category}:{window_minute}
  where window_minute = int(time.time()) // 60

Fails open when Redis is unavailable — requests are never blocked due to a
Redis failure. An ERROR log is written so on-call can investigate.
See docs/ARCHITECTURE.md — Rate Limiting, docs/ENV_CONFIG.md — RATE_LIMIT_*.
"""

import base64
import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings
from app.schemas import ErrorResponse

logger = logging.getLogger(__name__)

_AI_PREFIXES = ("/v1/jobs",)
_AUTH_PREFIXES = ("/v1/auth",)
_SKIP_PATHS = ("/health",)

_RATE_LIMIT_MESSAGE = "Too many requests. Please try again later."


def _classify(path: str) -> str:
    """Returns the rate limit tier for a request path."""
    if path in _SKIP_PATHS or path.startswith("/health/"):
        return "skip"
    for prefix in _AI_PREFIXES:
        if path.startswith(prefix):
            return "ai"
    for prefix in _AUTH_PREFIXES:
        if path.startswith(prefix):
            return "auth"
    return "general"


def _extract_sub(authorization: str) -> str | None:
    """
    Extracts the JWT sub claim without signature verification.

    Used only for rate-limit keying — the auth dependency performs full
    JWT validation later in the request cycle. A manipulated sub here
    can only affect the caller's own rate-limit bucket.
    """
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ")
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        sub = payload.get("sub")
        return sub if isinstance(sub, str) and sub else None
    except Exception:
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enforces per-user (or per-IP for auth routes) request rate limits.

    Reads app.state.redis on each dispatch — set during the app lifespan.
    If app.state.redis is None the middleware is a no-op (fail open).
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        category = _classify(request.url.path)
        if category == "skip":
            return await call_next(request)

        redis_client: Any | None = getattr(request.app.state, "redis", None)
        if redis_client is None:
            return await call_next(request)

        settings = get_settings()

        if category == "auth":
            identifier = (
                request.client.host if request.client else "unknown"
            ) or "unknown"
            limit = settings.rate_limit_auth
        else:
            sub = _extract_sub(request.headers.get("authorization", ""))
            identifier = (
                sub
                or (request.client.host if request.client else "unknown")
                or "unknown"
            )
            if category == "ai":
                limit = settings.rate_limit_ai
            else:
                limit = settings.rate_limit_general

        window = int(time.time()) // 60
        key = f"{identifier}:{category}:{window}"

        try:
            current: int = await redis_client.incr(key)
            if current == 1:
                await redis_client.expire(key, 60)
        except Exception as exc:
            logger.error(
                "Rate limiter Redis failure",
                extra={"error": str(exc), "key": key},
            )
            return await call_next(request)

        if current > limit:
            seconds_remaining = 60 - (int(time.time()) % 60)
            correlation_id = str(getattr(request.state, "correlation_id", ""))
            return JSONResponse(
                status_code=429,
                content=ErrorResponse(
                    error_code="rate_limit_exceeded",
                    message=_RATE_LIMIT_MESSAGE,
                    request_id=correlation_id,
                ).model_dump(),
                headers={"Retry-After": str(seconds_remaining)},
            )

        return await call_next(request)
