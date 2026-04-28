"""
auth.py
PRLifts Backend

FastAPI dependency for Supabase JWT authentication. get_current_user is the
single entry point for protected routes — add it as a Depends() parameter to
any route that requires a signed-in user.

The JWT value is never logged at any level. Only the resolved user_id is logged
on successful authentication. See docs/STANDARDS.md § 2.2 Hard Rules.
See docs/ERROR_CATALOG.md — Auth Errors for all error codes used here.
"""

import logging
from dataclasses import dataclass
from typing import NoReturn
from uuid import UUID

import jwt
from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.schemas import ErrorResponse

logger = logging.getLogger(__name__)

_ALGORITHM = "HS256"
_AUDIENCE = "authenticated"


@dataclass(frozen=True)
class AuthenticatedUser:
    """
    Validated user identity extracted from a Supabase JWT.

    Returned by get_current_user on success. The id maps to auth.uid() in
    PostgreSQL RLS policies and to the user.id primary key.
    """

    id: UUID
    role: str


def _raise_401(error_code: str, message: str, correlation_id: str) -> NoReturn:
    """
    Raises HTTP 401 with a standard ErrorResponse body.

    Args:
        error_code: Machine-readable code from docs/ERROR_CATALOG.md.
        message: User-safe message. Never include internal details.
        correlation_id: Request correlation ID for support queries.

    Raises:
        HTTPException: Always — HTTP 401 with the error body.
    """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=ErrorResponse(
            error_code=error_code,
            message=message,
            request_id=correlation_id,
        ).model_dump(),
    )


async def get_current_user(request: Request) -> AuthenticatedUser:
    """
    FastAPI dependency that validates a Supabase JWT and returns the caller's identity.

    Reads Authorization: Bearer <token>, decodes with SUPABASE_JWT_SECRET using
    HS256, and returns the authenticated user from the token claims.

    The raw JWT is never logged — only the resolved user_id is emitted on success.

    Args:
        request: The incoming FastAPI request.

    Returns:
        AuthenticatedUser with the validated user id and role.

    Raises:
        HTTPException 401 auth_token_missing: No Authorization header present.
        HTTPException 401 auth_token_expired: JWT is past its expiry time.
        HTTPException 401 auth_token_invalid: Signature invalid, malformed token,
            bad audience, or sub claim missing/non-UUID.
    """
    correlation_id: str = getattr(request.state, "correlation_id", "")

    auth_header: str = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        _raise_401("auth_token_missing", "Authentication required.", correlation_id)

    token = auth_header.removeprefix("Bearer ")
    secret = get_settings().supabase_jwt_secret

    try:
        payload: dict[str, object] = jwt.decode(
            token,
            secret,
            algorithms=[_ALGORITHM],
            audience=_AUDIENCE,
        )
    except jwt.ExpiredSignatureError:
        # Caught before InvalidTokenError because ExpiredSignatureError is a subclass.
        _raise_401(
            "auth_token_expired",
            "Your session has expired. Please sign in again.",
            correlation_id,
        )
    except jwt.InvalidTokenError:
        _raise_401(
            "auth_token_invalid",
            "Your session has expired. Please sign in again.",
            correlation_id,
        )

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        _raise_401(
            "auth_token_invalid",
            "Your session has expired. Please sign in again.",
            correlation_id,
        )

    try:
        user_id = UUID(sub)
    except ValueError:
        _raise_401(
            "auth_token_invalid",
            "Your session has expired. Please sign in again.",
            correlation_id,
        )

    role: str = str(payload.get("role", _AUDIENCE))

    logger.info("User authenticated", extra={"user_id": str(user_id)})
    return AuthenticatedUser(id=user_id, role=role)
