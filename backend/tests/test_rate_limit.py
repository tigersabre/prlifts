"""
test_rate_limit.py
PRLifts Backend Tests

Tests for the rate limiting middleware.

Covers:
  - _classify: endpoint tier classification
  - _extract_sub: JWT sub extraction without signature verification
  - RateLimitMiddleware: 429 on limit exceeded, Retry-After header,
    fail open on Redis unavailability, per-tier limits, IP fallback for auth routes.

Redis is injected by setting app.state.redis directly after the lifespan
has started (REDIS_URL is not set in tests, so lifespan sets it to None).
The autouse _restore_redis fixture resets it to None after each test.

See GitHub Issue #40 for acceptance criteria.
"""

import base64
import json
import os
import time
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("APP_VERSION", "0.1.0")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-supabase-jwt-secret-for-unit-tests")

from main import app  # noqa: E402

# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_fake_jwt(user_id: str) -> str:
    """
    Builds a minimal JWT with the given sub claim.

    The signature is intentionally invalid — _extract_sub only decodes
    the payload without verifying the signature.
    """
    header_bytes = b'{"alg":"HS256","typ":"JWT"}'
    header = base64.urlsafe_b64encode(header_bytes).rstrip(b"=").decode()
    payload_bytes = json.dumps({"sub": user_id}).encode()
    payload = base64.urlsafe_b64encode(payload_bytes).rstrip(b"=").decode()
    return f"{header}.{payload}.fakesig"


def _make_redis_mock(count: int = 1) -> MagicMock:
    """Returns a mock Redis client whose INCR always returns `count`."""
    mock = MagicMock()
    mock.incr = AsyncMock(return_value=count)
    mock.expire = AsyncMock(return_value=True)
    return mock


@pytest.fixture(autouse=True)
def _restore_redis() -> Generator[None, None, None]:
    """Resets app.state.redis to None after each test."""
    yield
    app.state.redis = None


# ── _classify ─────────────────────────────────────────────────────────────────


def test_classify_health_returns_skip() -> None:
    from app.middleware.rate_limit import _classify

    assert _classify("/health") == "skip"


def test_classify_health_subpath_returns_skip() -> None:
    from app.middleware.rate_limit import _classify

    assert _classify("/health/live") == "skip"


def test_classify_jobs_root_returns_ai() -> None:
    from app.middleware.rate_limit import _classify

    assert _classify("/v1/jobs") == "ai"


def test_classify_jobs_with_id_returns_ai() -> None:
    from app.middleware.rate_limit import _classify

    assert _classify("/v1/jobs/abc-123") == "ai"


def test_classify_auth_endpoint_returns_auth() -> None:
    from app.middleware.rate_limit import _classify

    assert _classify("/v1/auth/login") == "auth"


def test_classify_users_returns_general() -> None:
    from app.middleware.rate_limit import _classify

    assert _classify("/v1/users/me") == "general"


def test_classify_workouts_returns_general() -> None:
    from app.middleware.rate_limit import _classify

    assert _classify("/v1/workouts") == "general"


def test_classify_workout_sets_returns_general() -> None:
    from app.middleware.rate_limit import _classify

    assert _classify("/v1/workout-sets") == "general"


# ── _extract_sub ──────────────────────────────────────────────────────────────


def test_extract_sub_returns_sub_from_valid_jwt() -> None:
    from app.middleware.rate_limit import _extract_sub

    token = _make_fake_jwt("user-abc-123")
    assert _extract_sub(f"Bearer {token}") == "user-abc-123"


def test_extract_sub_returns_none_for_missing_bearer_prefix() -> None:
    from app.middleware.rate_limit import _extract_sub

    assert _extract_sub("token-without-bearer") is None


def test_extract_sub_returns_none_for_empty_string() -> None:
    from app.middleware.rate_limit import _extract_sub

    assert _extract_sub("") is None


def test_extract_sub_returns_none_for_malformed_jwt() -> None:
    from app.middleware.rate_limit import _extract_sub

    assert _extract_sub("Bearer not.a.valid.jwt.parts") is None


def test_extract_sub_returns_none_when_payload_has_no_sub() -> None:
    from app.middleware.rate_limit import _extract_sub

    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(b'{"role":"user"}').rstrip(b"=").decode()
    assert _extract_sub(f"Bearer {header}.{payload}.sig") is None


def test_extract_sub_returns_none_when_sub_is_not_a_string() -> None:
    from app.middleware.rate_limit import _extract_sub

    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(b'{"sub": 12345}').rstrip(b"=").decode()
    assert _extract_sub(f"Bearer {header}.{payload}.sig") is None


def test_extract_sub_returns_none_when_payload_is_invalid_base64() -> None:
    from app.middleware.rate_limit import _extract_sub

    assert _extract_sub("Bearer header.!!!invalid!!!.sig") is None


# ── Middleware: no Redis (fail open) ──────────────────────────────────────────


def test_middleware_allows_request_when_redis_is_none(client: TestClient) -> None:
    # app.state.redis is None (set by lifespan since REDIS_URL is not configured)
    response = client.get("/health")

    assert response.status_code == 200


# ── Middleware: rate limit not exceeded ────────────────────────────────────────


def test_general_endpoint_below_limit_returns_non_429(client: TestClient) -> None:
    app.state.redis = _make_redis_mock(count=1)
    response = client.get(
        "/v1/workouts",
        headers={"Authorization": f"Bearer {_make_fake_jwt('user-1')}"},
    )

    assert response.status_code != 429


def test_ai_endpoint_below_limit_returns_non_429(client: TestClient) -> None:
    app.state.redis = _make_redis_mock(count=1)
    response = client.get(
        "/v1/jobs/00000000-0000-0000-0000-000000000001",
        headers={"Authorization": f"Bearer {_make_fake_jwt('user-1')}"},
    )

    assert response.status_code != 429


# ── Middleware: rate limit exceeded ───────────────────────────────────────────


def test_general_endpoint_returns_429_when_limit_exceeded(client: TestClient) -> None:
    app.state.redis = _make_redis_mock(count=101)
    response = client.get(
        "/v1/workouts",
        headers={"Authorization": f"Bearer {_make_fake_jwt('user-1')}"},
    )

    assert response.status_code == 429


def test_ai_endpoint_returns_429_when_limit_exceeded(client: TestClient) -> None:
    app.state.redis = _make_redis_mock(count=11)
    response = client.get(
        "/v1/jobs/00000000-0000-0000-0000-000000000001",
        headers={"Authorization": f"Bearer {_make_fake_jwt('user-1')}"},
    )

    assert response.status_code == 429


def test_auth_endpoint_returns_429_when_ip_limit_exceeded(client: TestClient) -> None:
    app.state.redis = _make_redis_mock(count=6)
    response = client.post("/v1/auth/login")

    assert response.status_code == 429


def test_rate_limit_response_body_has_correct_error_code(client: TestClient) -> None:
    app.state.redis = _make_redis_mock(count=101)
    response = client.get(
        "/v1/workouts",
        headers={"Authorization": f"Bearer {_make_fake_jwt('user-1')}"},
    )

    assert response.json()["error_code"] == "rate_limit_exceeded"


def test_rate_limit_response_body_has_message(client: TestClient) -> None:
    app.state.redis = _make_redis_mock(count=101)
    response = client.get(
        "/v1/workouts",
        headers={"Authorization": f"Bearer {_make_fake_jwt('user-1')}"},
    )

    assert response.json()["message"] != ""


def test_rate_limit_response_body_has_request_id(client: TestClient) -> None:
    app.state.redis = _make_redis_mock(count=101)
    response = client.get(
        "/v1/workouts",
        headers={"Authorization": f"Bearer {_make_fake_jwt('user-1')}"},
    )

    body = response.json()
    assert "request_id" in body


def test_rate_limit_response_includes_retry_after_header(client: TestClient) -> None:
    app.state.redis = _make_redis_mock(count=101)
    response = client.get(
        "/v1/workouts",
        headers={"Authorization": f"Bearer {_make_fake_jwt('user-1')}"},
    )

    assert "retry-after" in response.headers


def test_retry_after_header_value_is_a_positive_integer(client: TestClient) -> None:
    app.state.redis = _make_redis_mock(count=101)
    response = client.get(
        "/v1/workouts",
        headers={"Authorization": f"Bearer {_make_fake_jwt('user-1')}"},
    )

    retry_after = int(response.headers["retry-after"])
    assert 0 < retry_after <= 60


def test_health_endpoint_is_never_rate_limited(client: TestClient) -> None:
    app.state.redis = _make_redis_mock(count=9999)
    response = client.get("/health")

    assert response.status_code == 200


# ── Middleware: Redis failure (fail open) ─────────────────────────────────────


def test_middleware_fails_open_when_redis_raises(client: TestClient) -> None:
    mock = MagicMock()
    mock.incr = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
    mock.expire = AsyncMock(return_value=True)
    app.state.redis = mock

    response = client.get("/health")

    assert response.status_code == 200


def test_middleware_fails_open_and_logs_error_on_redis_failure(
    client: TestClient,
) -> None:
    mock = MagicMock()
    mock.incr = AsyncMock(side_effect=OSError("connection refused"))
    app.state.redis = mock

    with patch("app.middleware.rate_limit.logger") as mock_logger:
        client.get(
            "/v1/workouts",
            headers={"Authorization": f"Bearer {_make_fake_jwt('user-1')}"},
        )
        mock_logger.error.assert_called_once()


# ── Middleware: identifier fallback ───────────────────────────────────────────


def test_general_endpoint_uses_ip_when_no_auth_header(client: TestClient) -> None:
    # No Authorization header — middleware falls back to request.client.host
    app.state.redis = _make_redis_mock(count=101)
    response = client.get("/v1/workouts")

    assert response.status_code == 429


def test_incr_is_called_with_expected_key_format(client: TestClient) -> None:
    mock = _make_redis_mock(count=1)
    app.state.redis = mock

    user_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    client.get(
        "/v1/workouts",
        headers={"Authorization": f"Bearer {_make_fake_jwt(user_id)}"},
    )

    window = int(time.time()) // 60
    expected_key = f"{user_id}:general:{window}"
    mock.incr.assert_called_once_with(expected_key)


def test_expire_called_on_first_request(client: TestClient) -> None:
    # When INCR returns 1, EXPIRE must be called to establish the TTL
    mock = _make_redis_mock(count=1)
    app.state.redis = mock

    client.get(
        "/v1/workouts",
        headers={"Authorization": f"Bearer {_make_fake_jwt('user-1')}"},
    )

    mock.expire.assert_called_once_with(
        mock.incr.call_args[0][0],
        60,
    )


def test_expire_not_called_on_subsequent_requests(client: TestClient) -> None:
    # When INCR returns > 1, key already has a TTL — EXPIRE must not reset it
    mock = _make_redis_mock(count=5)
    app.state.redis = mock

    client.get(
        "/v1/workouts",
        headers={"Authorization": f"Bearer {_make_fake_jwt('user-1')}"},
    )

    mock.expire.assert_not_called()
