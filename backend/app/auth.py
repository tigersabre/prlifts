"""
auth.py
PRLifts Backend

FastAPI dependency for Supabase JWT authentication. get_current_user is the
single entry point for protected routes — add it as a Depends() parameter to
any route that requires a signed-in user.

Verifies ES256 tokens via Supabase's JWKS endpoint (1-hour TTL cache). Falls
back to HS256 with SUPABASE_JWT_SECRET for legacy tokens when the secret is
set and the token algorithm is not ES256.

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
from app.jwks import get_public_key
from app.schemas import ErrorResponse

logger = logging.getLogger(__name__)

_AUDIENCE = "authenticated"
_MSG_EXPIRED = "Your session has expired. Please sign in again."
_MSG_INVALID = "Your session has expired. Please sign in again."


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
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=ErrorResponse(
            error_code=error_code,
            message=message,
            request_id=correlation_id,
        ).model_dump(),
    )


async def _verify_es256(token: str, kid: str, correlation_id: str) -> dict[str, object]:
    """Decodes an ES256 token using the matching public key from JWKS."""
    public_key = await get_public_key(kid)
    if public_key is None:
        _raise_401("auth_token_invalid", _MSG_INVALID, correlation_id)
    try:
        return jwt.decode(
            token,
            public_key,
            algorithms=["ES256"],
            audience=_AUDIENCE,
        )
    except jwt.ExpiredSignatureError:
        _raise_401("auth_token_expired", _MSG_EXPIRED, correlation_id)
    except jwt.InvalidTokenError:
        _raise_401("auth_token_invalid", _MSG_INVALID, correlation_id)


def _verify_hs256(token: str, correlation_id: str) -> dict[str, object]:
    """Decodes an HS256 token using SUPABASE_JWT_SECRET."""
    secret = get_settings().supabase_jwt_secret
    if not secret:
        _raise_401("auth_token_invalid", _MSG_INVALID, correlation_id)
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=_AUDIENCE,
        )
    except jwt.ExpiredSignatureError:
        _raise_401("auth_token_expired", _MSG_EXPIRED, correlation_id)
    except jwt.InvalidTokenError:
        _raise_401("auth_token_invalid", _MSG_INVALID, correlation_id)


async def get_current_user(request: Request) -> AuthenticatedUser:
    """
    FastAPI dependency that validates a Supabase JWT and returns the caller's
    identity.

    Verifies ES256 tokens via the Supabase JWKS endpoint (1-hour TTL cache).
    Falls back to HS256 with SUPABASE_JWT_SECRET when the secret is set and
    the token algorithm is not ES256.

    The raw JWT is never logged — only the resolved user_id is emitted on
    success.

    Args:
        request: The incoming FastAPI request.

    Returns:
        AuthenticatedUser with the validated user id and role.

    Raises:
        HTTPException 401 auth_token_missing: No Authorization header.
        HTTPException 401 auth_token_expired: JWT past its expiry time.
        HTTPException 401 auth_token_invalid: Bad signature, malformed token,
            wrong audience, or sub claim missing/non-UUID.
    """
    correlation_id: str = getattr(request.state, "correlation_id", "")

    auth_header: str = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        _raise_401("auth_token_missing", "Authentication required.", correlation_id)

    token = auth_header.removeprefix("Bearer ")

    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError:
        _raise_401("auth_token_invalid", _MSG_INVALID, correlation_id)

    alg: str = unverified_header.get("alg", "")
    kid: str = unverified_header.get("kid", "")

    if alg == "ES256":
        if not kid:
            _raise_401("auth_token_invalid", _MSG_INVALID, correlation_id)
        payload: dict[str, object] = await _verify_es256(token, kid, correlation_id)
    else:
        payload = _verify_hs256(token, correlation_id)

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        _raise_401("auth_token_invalid", _MSG_INVALID, correlation_id)

    try:
        user_id = UUID(sub)
    except ValueError:
        _raise_401("auth_token_invalid", _MSG_INVALID, correlation_id)

    role: str = str(payload.get("role", _AUDIENCE))

    logger.info("User authenticated", extra={"user_id": str(user_id)})
    return AuthenticatedUser(id=user_id, role=role)
