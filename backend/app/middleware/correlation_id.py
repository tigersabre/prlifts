"""
correlation_id.py
PRLifts Backend

Starlette middleware that assigns a UUID correlation_id to every incoming
request. The ID is stored in request.state for downstream use, injected into
the logging context so all log lines carry it, and returned in the
X-Correlation-ID response header for client-side debugging and support queries.
See docs/STANDARDS.md § 4.6 Correlation ID Standard.
"""

import logging
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.logging_config import set_correlation_id

logger = logging.getLogger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Assigns a UUID correlation_id to each request.

    Places the ID in request.state.correlation_id, the logging ContextVar,
    and the X-Correlation-ID response header.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """
        Generates correlation_id, injects it into request state and log context,
        then delegates to the next handler.

        Args:
            request: The incoming HTTP request.
            call_next: The next handler in the middleware chain.

        Returns:
            HTTP response with X-Correlation-ID header set.
        """
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        set_correlation_id(correlation_id)

        logger.info(
            "Request received",
            extra={
                "endpoint": request.url.path,
                "method": request.method,
            },
        )

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
