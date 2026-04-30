"""
workouts.py
PRLifts Backend

Workout CRUD endpoints. Creates, lists, reads, updates, and deletes Workout
records for the authenticated user.

user_id is always taken from the JWT sub — never from the request body or URL
path. PATCH and DELETE verify the caller owns the target workout and return
HTTP 403 for any attempt to access another user's data (IDOR protection).

See docs/SCHEMA.md — workout table.
See docs/ERROR_CATALOG.md — workout_ error codes.
See docs/api/openapi.yaml — /v1/workouts paths.
"""

import logging
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth import AuthenticatedUser, get_current_user
from app.repositories.workout_repository import (
    WorkoutRecord,
    WorkoutRepository,
    get_workout_repository,
)
from app.schemas import (
    CreateWorkoutRequest,
    ErrorResponse,
    UpdateWorkoutRequest,
    WorkoutListResponse,
    WorkoutResponse,
    WorkoutStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workouts", tags=["workouts"])


def _correlation_id(request: Request) -> str:
    return str(getattr(request.state, "correlation_id", ""))


def _workout_record_to_response(record: WorkoutRecord) -> WorkoutResponse:
    return WorkoutResponse.model_validate(record, from_attributes=True)


def _raise_workout_not_found(correlation_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorResponse(
            error_code="workout_not_found",
            message="Workout not found.",
            request_id=correlation_id,
        ).model_dump(),
    )


def _raise_workout_forbidden(correlation_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=ErrorResponse(
            error_code="workout_forbidden",
            message="You do not have access to this workout.",
            request_id=correlation_id,
        ).model_dump(),
    )


def _check_ownership(
    record: WorkoutRecord | None,
    user_id: UUID,
    correlation_id: str,
) -> WorkoutRecord:
    """Return the record if it exists and is owned by user_id; raise otherwise."""
    if record is None:
        _raise_workout_not_found(correlation_id)
    assert record is not None
    if record.user_id != user_id:
        _raise_workout_forbidden(correlation_id)
    return record


# ── POST /v1/workouts ─────────────────────────────────────────────────────────


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=WorkoutResponse,
    summary="Create a new workout",
    description=(
        "Creates a workout with status in_progress. "
        "user_id is taken from the JWT sub. "
        "server_received_at is assigned server-side for conflict resolution."
    ),
)
async def create_workout(
    body: CreateWorkoutRequest,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    repo: Annotated[WorkoutRepository, Depends(get_workout_repository)],
) -> WorkoutResponse:
    record = await repo.create(
        user_id=current_user.id,
        workout_type=body.type.value,
        workout_format=body.format.value,
        name=body.name,
        location=body.location.value if body.location is not None else None,
        plan_id=body.plan_id,
        client_started_at=body.client_started_at,
    )
    logger.info(
        "Workout created",
        extra={"user_id": str(current_user.id), "workout_id": str(record.id)},
    )
    return _workout_record_to_response(record)


# ── GET /v1/workouts ──────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=WorkoutListResponse,
    summary="List workouts for current user",
    description=(
        "Returns all workouts for the authenticated user ordered by started_at DESC."
    ),
)
async def list_workouts(
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    repo: Annotated[WorkoutRepository, Depends(get_workout_repository)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    format: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> WorkoutListResponse:
    records, total = await repo.list_for_user(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        format_filter=format,
        status_filter=status,
    )
    return WorkoutListResponse(
        data=[_workout_record_to_response(r) for r in records],
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )


# ── GET /v1/workouts/{workout_id} ─────────────────────────────────────────────


@router.get(
    "/{workout_id}",
    response_model=WorkoutResponse,
    summary="Get workout by ID",
    description=(
        "Returns the workout if it belongs to the authenticated user. "
        "Returns HTTP 403 if the workout exists but is owned by another user."
    ),
)
async def get_workout(
    workout_id: UUID,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    repo: Annotated[WorkoutRepository, Depends(get_workout_repository)],
) -> WorkoutResponse:
    cid = _correlation_id(request)
    record = await repo.get_by_id(workout_id)
    owned = _check_ownership(record, current_user.id, cid)
    logger.info(
        "Workout fetched",
        extra={"user_id": str(current_user.id), "workout_id": str(workout_id)},
    )
    return _workout_record_to_response(owned)


# ── PATCH /v1/workouts/{workout_id} ──────────────────────────────────────────


@router.patch(
    "/{workout_id}",
    response_model=WorkoutResponse,
    summary="Update workout",
    description=(
        "Partially updates the workout. Only fields present in the request body "
        "are modified. When status is set to completed, completed_at and "
        "duration_seconds are assigned server-side."
    ),
)
async def update_workout(
    workout_id: UUID,
    body: UpdateWorkoutRequest,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    repo: Annotated[WorkoutRepository, Depends(get_workout_repository)],
) -> WorkoutResponse:
    cid = _correlation_id(request)
    record = await repo.get_by_id(workout_id)
    owned = _check_ownership(record, current_user.id, cid)

    updates: dict[str, object] = {}
    for field in body.model_fields_set:
        value = getattr(body, field)
        updates[field] = value.value if hasattr(value, "value") else value

    if updates.get("status") == WorkoutStatus.completed.value:
        now = datetime.now(UTC)
        updates["completed_at"] = now
        started_at = owned.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=UTC)
        updates["duration_seconds"] = int((now - started_at).total_seconds())

    if updates:
        updated = await repo.update(workout_id, updates)
    else:
        updated = owned

    assert updated is not None
    logger.info(
        "Workout updated",
        extra={"user_id": str(current_user.id), "workout_id": str(workout_id)},
    )
    return _workout_record_to_response(updated)


# ── DELETE /v1/workouts/{workout_id} ─────────────────────────────────────────


@router.delete(
    "/{workout_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete workout",
    description=(
        "Deletes the workout and cascades to workout_exercise and workout_set rows. "
        "PersonalRecords derived from the deleted sets are recalculated. "
        "Returns HTTP 403 if the workout exists but is owned by another user."
    ),
)
async def delete_workout(
    workout_id: UUID,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    repo: Annotated[WorkoutRepository, Depends(get_workout_repository)],
) -> None:
    cid = _correlation_id(request)
    record = await repo.get_by_id(workout_id)
    _check_ownership(record, current_user.id, cid)

    await repo.delete(workout_id)
    logger.info(
        "Workout deleted",
        extra={"user_id": str(current_user.id), "workout_id": str(workout_id)},
    )
