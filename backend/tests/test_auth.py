"""
test_auth.py
PRLifts Backend Tests

Unit tests for app/auth.py: all four JWT validation scenarios defined in
docs/ERROR_CATALOG.md, credential safety (JWT value never in logs), and the
shared ErrorResponse schema.

get_current_user is tested by calling it directly as an async function with
a minimal mock Request — no HTTP round-trip needed for these unit tests.
"""

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID

import jwt
import pytest
from fastapi import HTTPException


def _detail(exc: HTTPException) -> dict[str, str]:
    """
    Extracts the error detail dict from an HTTPException.

    Starlette 1.0.0 annotates HTTPException.detail as str rather than Any,
    so a single type: ignore here keeps every test assertion clean.
    """
    return exc.detail  # type: ignore[return-value]


# ── Test fixtures ─────────────────────────────────────────────────────────────

_SECRET: str = os.environ.get(
    "SUPABASE_JWT_SECRET", "test-supabase-jwt-secret-for-unit-tests"
)
_TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"
_ALGORITHM = "HS256"
_AUDIENCE = "authenticated"


def _make_token(
    *,
    user_id: str | None = _TEST_USER_ID,
    expired: bool = False,
    audience: str = _AUDIENCE,
    secret: str = _SECRET,
) -> str:
    """
    Encodes a test JWT signed with the test secret.

    Args:
        user_id: Value for the sub claim. Pass None to omit the claim.
        expired: If True, sets exp one hour in the past.
        audience: Value for the aud claim.
        secret: Signing secret (defaults to the test secret from env).

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(UTC)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    payload: dict[str, Any] = {
        "exp": exp,
        "aud": audience,
        "role": "authenticated",
    }
    if user_id is not None:
        payload["sub"] = user_id
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def _make_request(
    authorization: str | None = None,
    correlation_id: str = "test-correlation-id",
) -> MagicMock:
    """
    Builds a minimal mock Request for testing get_current_user directly.

    Only the two attributes get_current_user reads are wired up:
    request.headers.get("authorization", "") and request.state.correlation_id.

    Args:
        authorization: Full header value, e.g. "Bearer <token>". None omits it.
        correlation_id: Value stored on request.state.

    Returns:
        MagicMock that behaves like a Starlette Request for auth purposes.
    """
    headers: dict[str, str] = {}
    if authorization is not None:
        headers["authorization"] = authorization

    req = MagicMock()
    req.headers.get = lambda key, default="": headers.get(key, default)
    req.state.correlation_id = correlation_id
    return req


# ── Happy path ────────────────────────────────────────────────────────────────


async def test_get_current_user_returns_authenticated_user_for_valid_jwt() -> None:
    # Arrange
    from app.auth import AuthenticatedUser, get_current_user

    token = _make_token()
    request = _make_request(authorization=f"Bearer {token}")

    # Act
    user = await get_current_user(request)

    # Assert
    assert isinstance(user, AuthenticatedUser)
    assert user.id == UUID(_TEST_USER_ID)
    assert user.role == "authenticated"


async def test_get_current_user_user_id_matches_sub_claim() -> None:
    # Arrange
    from app.auth import get_current_user

    other_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    token = _make_token(user_id=other_id)
    request = _make_request(authorization=f"Bearer {token}")

    # Act
    user = await get_current_user(request)

    # Assert
    assert user.id == UUID(other_id)


# ── Missing token ─────────────────────────────────────────────────────────────


async def test_get_current_user_raises_401_auth_token_missing_when_no_header() -> None:
    # Arrange
    from app.auth import get_current_user

    request = _make_request(authorization=None)

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request)

    assert exc_info.value.status_code == 401
    assert _detail(exc_info.value)["error_code"] == "auth_token_missing"
    assert _detail(exc_info.value)["message"] == "Authentication required."


async def test_get_current_user_raises_token_missing_when_no_bearer_prefix() -> None:
    # Arrange — header present but not Bearer-prefixed
    from app.auth import get_current_user

    token = _make_token()
    request = _make_request(authorization=token)  # missing "Bearer " prefix

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request)

    assert exc_info.value.status_code == 401
    assert _detail(exc_info.value)["error_code"] == "auth_token_missing"


# ── Expired token ─────────────────────────────────────────────────────────────


async def test_get_current_user_raises_401_auth_token_expired_for_past_exp() -> None:
    # Arrange
    from app.auth import get_current_user

    token = _make_token(expired=True)
    request = _make_request(authorization=f"Bearer {token}")

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request)

    assert exc_info.value.status_code == 401
    assert _detail(exc_info.value)["error_code"] == "auth_token_expired"
    assert "expired" in _detail(exc_info.value)["message"].lower()


# ── Invalid / malformed token ─────────────────────────────────────────────────


async def test_get_current_user_raises_401_auth_token_invalid_for_garbage_string() -> (
    None
):
    # Arrange
    from app.auth import get_current_user

    request = _make_request(authorization="Bearer not-a-real-jwt-at-all")

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request)

    assert exc_info.value.status_code == 401
    assert _detail(exc_info.value)["error_code"] == "auth_token_invalid"


async def test_get_current_user_raises_401_auth_token_invalid_for_wrong_secret() -> (
    None
):
    # Arrange — valid JWT structure but signed with a different secret
    from app.auth import get_current_user

    token = _make_token(secret="completely-different-secret-xxxxxxxxxx")
    request = _make_request(authorization=f"Bearer {token}")

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request)

    assert exc_info.value.status_code == 401
    assert _detail(exc_info.value)["error_code"] == "auth_token_invalid"


async def test_get_current_user_raises_401_auth_token_invalid_when_sub_is_missing() -> (
    None
):
    # Arrange — valid signature but no sub claim
    from app.auth import get_current_user

    token = _make_token(user_id=None)
    request = _make_request(authorization=f"Bearer {token}")

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request)

    assert exc_info.value.status_code == 401
    assert _detail(exc_info.value)["error_code"] == "auth_token_invalid"


async def test_get_current_user_raises_token_invalid_when_sub_is_not_a_uuid() -> None:
    # Arrange — sub is present but not a valid UUID
    from app.auth import get_current_user

    token = _make_token(user_id="not-a-uuid")
    request = _make_request(authorization=f"Bearer {token}")

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request)

    assert exc_info.value.status_code == 401
    assert _detail(exc_info.value)["error_code"] == "auth_token_invalid"


# ── Error response structure ──────────────────────────────────────────────────


async def test_error_response_includes_correlation_id_as_request_id() -> None:
    # Arrange
    from app.auth import get_current_user

    request = _make_request(authorization=None, correlation_id="my-correlation-id")

    # Act + Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request)

    assert _detail(exc_info.value)["request_id"] == "my-correlation-id"


# ── Credential safety ─────────────────────────────────────────────────────────


async def test_get_current_user_never_logs_jwt_value(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange
    from app.auth import get_current_user

    token = _make_token()
    request = _make_request(authorization=f"Bearer {token}")

    # Act
    with caplog.at_level(logging.DEBUG):
        await get_current_user(request)

    # Assert — the raw JWT must not appear in any log record at any level
    for record in caplog.records:
        assert token not in record.getMessage()
        assert token not in str(record.__dict__)


async def test_get_current_user_logs_user_id_on_success(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange
    from app.auth import get_current_user

    token = _make_token()
    request = _make_request(authorization=f"Bearer {token}")

    # Act
    with caplog.at_level(logging.INFO, logger="app.auth"):
        await get_current_user(request)

    # Assert — user_id appears in logs, JWT does not
    log_output = " ".join(r.getMessage() for r in caplog.records)
    assert _TEST_USER_ID in log_output or any(
        _TEST_USER_ID in str(r.__dict__) for r in caplog.records
    )


# ── ErrorResponse schema ──────────────────────────────────────────────────────


def test_error_response_serialises_all_fields() -> None:
    # Arrange
    from app.schemas import ErrorResponse

    # Act
    response = ErrorResponse(
        error_code="auth_token_missing",
        message="Authentication required.",
        request_id="abc-123",
    )

    # Assert
    data = response.model_dump()
    assert data == {
        "error_code": "auth_token_missing",
        "message": "Authentication required.",
        "request_id": "abc-123",
    }
