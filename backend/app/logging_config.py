"""
logging_config.py
PRLifts Backend

Structured JSON logging configuration. Every log line carries correlation_id,
level, message, and logger name. The correlation_id is stored in a ContextVar
set per-request by CorrelationIDMiddleware, so it propagates automatically to
all log calls within that request without explicit threading.
See docs/STANDARDS.md § 2.4 Unified Log Level Standard.
"""

import json
import logging
import uuid
from contextvars import ContextVar
from typing import Any

_correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

# Standard LogRecord attributes excluded from the extra JSON fields.
_EXCLUDED_LOG_ATTRS = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)


def set_correlation_id(value: str) -> None:
    """
    Sets the correlation_id for the current async context.

    Called by CorrelationIDMiddleware on each incoming request.

    Args:
        value: UUID string identifying the current request.
    """
    _correlation_id_var.set(value)


def get_correlation_id() -> str:
    """
    Returns the correlation_id for the current async context.

    Generates a new UUID if none has been set (e.g. background tasks
    or code paths outside a request context).

    Returns:
        Correlation ID string.
    """
    return _correlation_id_var.get() or str(uuid.uuid4())


class JSONFormatter(logging.Formatter):
    """Formats log records as structured JSON lines with correlation_id."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Serialises a log record to a JSON string.

        Includes all extra fields passed via logging's extra={} parameter.

        Args:
            record: The log record to format.

        Returns:
            JSON-encoded log line string.
        """
        record.message = record.getMessage()
        log_data: dict[str, Any] = {
            "level": record.levelname,
            "message": record.message,
            "logger": record.name,
            "correlation_id": get_correlation_id(),
        }
        for key, value in record.__dict__.items():
            if key not in _EXCLUDED_LOG_ATTRS:
                log_data[key] = value
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configures the root logger with the JSON formatter.

    Called once on application startup via the lifespan context manager.
    Uses force=True so it replaces any handlers already attached (e.g. uvicorn's).

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        handlers=[handler],
        force=True,
    )
