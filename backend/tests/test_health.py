"""
test_health.py
PRLifts Backend Tests

Tests for the health check endpoint, correlation ID middleware, app startup
(APScheduler, Sentry init), and structured logging (JSONFormatter, correlation_id).
"""

import json
import logging
import sys
from unittest.mock import patch

from fastapi.testclient import TestClient

# ── Health endpoint ────────────────────────────────────────────────────────────


def test_health_check_returns_200_on_get(client: TestClient) -> None:
    # Arrange + Act
    response = client.get("/health")

    # Assert
    assert response.status_code == 200


def test_health_check_response_body_matches_spec(client: TestClient) -> None:
    # Arrange + Act
    response = client.get("/health")

    # Assert
    assert response.json() == {"status": "ok", "environment": "test"}


def test_health_check_response_content_type_is_json(client: TestClient) -> None:
    # Arrange + Act
    response = client.get("/health")

    # Assert
    assert "application/json" in response.headers["content-type"]


# ── Correlation ID middleware ──────────────────────────────────────────────────


def test_health_check_response_includes_correlation_id_header(
    client: TestClient,
) -> None:
    # Arrange + Act
    response = client.get("/health")

    # Assert
    assert "x-correlation-id" in response.headers


def test_correlation_id_header_is_a_valid_uuid(client: TestClient) -> None:
    # Arrange
    import uuid

    # Act
    response = client.get("/health")

    # Assert — raises ValueError if not a valid UUID
    uuid.UUID(response.headers["x-correlation-id"])


def test_each_request_receives_a_unique_correlation_id(client: TestClient) -> None:
    # Arrange + Act
    first = client.get("/health")
    second = client.get("/health")

    # Assert
    assert first.headers["x-correlation-id"] != second.headers["x-correlation-id"]


# ── App startup ────────────────────────────────────────────────────────────────


def test_scheduler_is_running_after_app_startup(client: TestClient) -> None:
    # Arrange
    from main import scheduler

    # Act — client fixture has already run the lifespan

    # Assert
    assert scheduler.running


def test_app_startup_completes_without_errors(client: TestClient) -> None:
    # Arrange + Act — client fixture exercises the full lifespan
    response = client.get("/health")

    # Assert — reaching here confirms startup succeeded
    assert response.status_code == 200


# ── Sentry initialisation ─────────────────────────────────────────────────────


def test_init_sentry_is_noop_when_dsn_is_empty() -> None:
    # Arrange
    from main import _init_sentry

    # Act + Assert — no exception raised, sentry_sdk.init never called
    with patch("sentry_sdk.init") as mock_init:
        _init_sentry("", "test")
        mock_init.assert_not_called()


def test_init_sentry_initialises_sdk_when_dsn_is_provided() -> None:
    # Arrange
    from main import _init_sentry

    fake_dsn = "https://publickey@sentry.io/123"

    # Act
    with patch("sentry_sdk.init") as mock_init:
        _init_sentry(fake_dsn, "staging")

        # Assert
        mock_init.assert_called_once()
        kwargs = mock_init.call_args.kwargs
        assert kwargs["dsn"] == fake_dsn
        assert kwargs["send_default_pii"] is False
        assert kwargs["environment"] == "staging"


# ── Structured logging ─────────────────────────────────────────────────────────


def test_json_formatter_produces_valid_json() -> None:
    # Arrange
    from app.logging_config import JSONFormatter

    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    # Act
    output = formatter.format(record)

    # Assert
    parsed = json.loads(output)
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test message"
    assert parsed["logger"] == "test.logger"
    assert "correlation_id" in parsed


def test_json_formatter_includes_exception_info_when_present() -> None:
    # Arrange
    from app.logging_config import JSONFormatter

    formatter = JSONFormatter()
    try:
        raise ValueError("deliberate test error")
    except ValueError:
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test.logger",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="Something failed",
        args=(),
        exc_info=exc_info,
    )

    # Act
    output = formatter.format(record)

    # Assert
    parsed = json.loads(output)
    assert "exception" in parsed
    assert "ValueError" in parsed["exception"]


def test_json_formatter_includes_extra_fields() -> None:
    # Arrange
    from app.logging_config import JSONFormatter

    formatter = JSONFormatter()
    # makeLogRecord sets entries directly into __dict__, so extra keys like
    # user_id land on the record without any attribute-assignment type issues.
    record = logging.makeLogRecord(
        {
            "name": "test.logger",
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": "Event",
            "args": (),
            "exc_info": None,
            "user_id": "abc-123",
        }
    )

    # Act
    output = formatter.format(record)

    # Assert
    parsed = json.loads(output)
    assert parsed["user_id"] == "abc-123"


def test_set_and_get_correlation_id_round_trips() -> None:
    # Arrange
    from app.logging_config import get_correlation_id, set_correlation_id

    expected = "my-test-correlation-id"

    # Act
    set_correlation_id(expected)
    result = get_correlation_id()

    # Assert
    assert result == expected


def test_get_correlation_id_returns_valid_uuid_when_not_set() -> None:
    # Arrange
    import uuid

    from app.logging_config import get_correlation_id, set_correlation_id

    set_correlation_id("")  # reset to empty

    # Act
    result = get_correlation_id()

    # Assert — raises ValueError if not a valid UUID format
    uuid.UUID(result)


def test_configure_logging_applies_requested_log_level() -> None:
    # Arrange
    from app.logging_config import configure_logging

    # Act
    configure_logging("WARNING")

    # Assert
    assert logging.root.level == logging.WARNING

    # Restore to avoid affecting other tests
    configure_logging("DEBUG")


# ── Settings ───────────────────────────────────────────────────────────────────


def test_settings_reads_environment_from_env_var() -> None:
    # Arrange + Act
    from app.config import get_settings

    settings = get_settings()

    # Assert
    assert settings.environment == "test"


def test_settings_reads_app_version_from_env_var() -> None:
    # Arrange + Act
    from app.config import get_settings

    settings = get_settings()

    # Assert
    assert settings.app_version == "0.1.0"
