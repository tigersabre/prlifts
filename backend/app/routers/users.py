"""
users.py
PRLifts Backend

User profile endpoints. Creates and manages the app-level User record that
is distinct from the Supabase Auth record. Supabase Auth creates the auth
identity; POST /v1/users creates the app profile that all other entities
(workouts, PRs) hang from.

All endpoints require a valid Supabase JWT. user_id is always taken from
the JWT sub — never from the request body or URL path. This prevents IDOR:
a caller can only ever read or modify their own profile.

See docs/SCHEMA.md — user table.
See docs/ERROR_CATALOG.md — auth_ and user_ error codes.
See docs/api/openapi.yaml — /v1/users paths.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import AuthenticatedUser, get_current_user
from app.repositories.user_repository import (
    UserRecord,
    UserRepository,
    get_user_repository,
)
from app.schemas import (
    CreateUserRequest,
    ErrorResponse,
    UpdateUserRequest,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

# Non-nullable user fields: never stored as NULL even if the client sends null.
_NON_NULLABLE_FIELDS = frozenset({"unit_preference", "measurement_unit", "gender"})


def _correlation_id(request: Request) -> str:
    return str(getattr(request.state, "correlation_id", ""))


def _user_record_to_response(record: UserRecord) -> UserResponse:
    return UserResponse.model_validate(record, from_attributes=True)


def _raise_user_not_found(correlation_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorResponse(
            error_code="user_not_found",
            message="User not found.",
            request_id=correlation_id,
        ).model_dump(),
    )


# ── POST /v1/users ────────────────────────────────────────────────────────────


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    summary="Create user profile",
    description=(
        "Creates the app-level user profile after Supabase Auth has created "
        "the auth record. user_id is taken from the JWT sub. "
        "Returns HTTP 409 if a profile already exists for this user."
    ),
)
async def create_user(
    body: CreateUserRequest,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserResponse:
    """
    Creates the app-level User record for an authenticated caller.

    Returns:
        HTTP 201 with the created UserResponse.

    Raises:
        HTTPException 422 user_display_name_too_long: display_name exceeds 50 chars.
        HTTPException 409 user_profile_exists: Profile already exists for this user.
    """
    cid = _correlation_id(request)

    if body.display_name is not None and len(body.display_name) > 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=ErrorResponse(
                error_code="user_display_name_too_long",
                message="Display name must be 50 characters or fewer.",
                request_id=cid,
            ).model_dump(),
        )

    if await repo.exists(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error_code="user_profile_exists",
                message="A profile already exists for this account.",
                request_id=cid,
            ).model_dump(),
        )

    record = await repo.create(
        user_id=current_user.id,
        display_name=body.display_name,
        unit_preference=body.unit_preference.value,
        measurement_unit=body.measurement_unit.value,
    )

    logger.info(
        "User profile created",
        extra={"user_id": str(current_user.id)},
    )
    return _user_record_to_response(record)


# ── GET /v1/users/me ──────────────────────────────────────────────────────────


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the profile for the authenticated user.",
)
async def get_me(
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserResponse:
    """
    Returns the authenticated user's profile.

    Returns:
        HTTP 200 with UserResponse.

    Raises:
        HTTPException 404 user_not_found: No profile exists for this user.
    """
    record = await repo.get_by_id(current_user.id)
    if record is None:
        _raise_user_not_found(_correlation_id(request))

    assert record is not None
    logger.info("User profile fetched", extra={"user_id": str(current_user.id)})
    return _user_record_to_response(record)


# ── PATCH /v1/users/me ────────────────────────────────────────────────────────


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description=(
        "Partially updates the authenticated user's profile. "
        "Only fields present in the request body are modified."
    ),
)
async def update_me(
    body: UpdateUserRequest,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserResponse:
    """
    Partially updates the authenticated user's profile.

    Fields absent from the request body are left unchanged. Nullable fields
    (display_name, date_of_birth, goal) may be explicitly set to null to
    clear them. Non-nullable fields are ignored if sent as null.

    Returns:
        HTTP 200 with the updated UserResponse.

    Raises:
        HTTPException 422 user_display_name_too_long: display_name exceeds 50 chars.
        HTTPException 404 user_not_found: No profile exists for this user.
    """
    cid = _correlation_id(request)

    if (
        "display_name" in body.model_fields_set
        and body.display_name is not None
        and len(body.display_name) > 50
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=ErrorResponse(
                error_code="user_display_name_too_long",
                message="Display name must be 50 characters or fewer.",
                request_id=cid,
            ).model_dump(),
        )

    updates: dict[str, object] = {}
    for field in body.model_fields_set:
        value = getattr(body, field)
        if field in _NON_NULLABLE_FIELDS and value is None:
            continue
        updates[field] = value.value if hasattr(value, "value") else value

    record: UserRecord | None = None
    if updates:
        record = await repo.update(current_user.id, updates)
    else:
        record = await repo.get_by_id(current_user.id)

    if record is None:
        _raise_user_not_found(cid)

    assert record is not None
    logger.info("User profile updated", extra={"user_id": str(current_user.id)})
    return _user_record_to_response(record)
