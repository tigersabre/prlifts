"""
workout_exercises.py
PRLifts Backend

WorkoutExercise CRUD endpoints.

POST /v1/workout-exercises — adds an exercise to a workout
DELETE /v1/workout-exercises/{id} — removes an exercise from a workout

user_id is always taken from the JWT sub. Ownership is verified by checking
that the target workout belongs to the authenticated user. HTTP 403 is returned
for any attempt to access another user's data (IDOR protection).

See docs/SCHEMA.md — workout_exercise table.
See docs/api/openapi.yaml — /v1/workout-exercises paths.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import AuthenticatedUser, get_current_user
from app.repositories.workout_exercise_repository import (
    WorkoutExerciseRecord,
    WorkoutExerciseRepository,
    get_workout_exercise_repository,
)
from app.repositories.workout_repository import (
    WorkoutRepository,
    get_workout_repository,
)
from app.schemas import (
    CreateWorkoutExerciseRequest,
    ErrorResponse,
    WorkoutExerciseResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workout-exercises", tags=["workout-exercises"])


def _correlation_id(request: Request) -> str:
    return str(getattr(request.state, "correlation_id", ""))


def _exercise_record_to_response(
    record: WorkoutExerciseRecord,
) -> WorkoutExerciseResponse:
    return WorkoutExerciseResponse.model_validate(record, from_attributes=True)


def _raise_not_found(correlation_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorResponse(
            error_code="workout_exercise_not_found",
            message="Workout exercise not found.",
            request_id=correlation_id,
        ).model_dump(),
    )


def _raise_forbidden(correlation_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=ErrorResponse(
            error_code="workout_exercise_forbidden",
            message="You do not have access to this workout exercise.",
            request_id=correlation_id,
        ).model_dump(),
    )


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


# ── POST /v1/workout-exercises ────────────────────────────────────────────────


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=WorkoutExerciseResponse,
    summary="Add exercise to workout",
    description=(
        "Creates a WorkoutExercise linking the given exercise to the given workout. "
        "The workout must belong to the authenticated user."
    ),
)
async def create_workout_exercise(
    body: CreateWorkoutExerciseRequest,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    exercise_repo: Annotated[
        WorkoutExerciseRepository, Depends(get_workout_exercise_repository)
    ],
    workout_repo: Annotated[WorkoutRepository, Depends(get_workout_repository)],
) -> WorkoutExerciseResponse:
    cid = _correlation_id(request)

    workout = await workout_repo.get_by_id(body.workout_id)
    if workout is None:
        _raise_workout_not_found(cid)
    assert workout is not None
    if workout.user_id != current_user.id:
        _raise_workout_forbidden(cid)

    record = await exercise_repo.create(
        workout_id=body.workout_id,
        user_id=current_user.id,
        exercise_id=body.exercise_id,
        order_index=body.order_index,
        notes=body.notes,
        rest_seconds=body.rest_seconds,
    )
    logger.info(
        "WorkoutExercise created",
        extra={
            "user_id": str(current_user.id),
            "workout_exercise_id": str(record.id),
            "workout_id": str(body.workout_id),
        },
    )
    return _exercise_record_to_response(record)


# ── DELETE /v1/workout-exercises/{workout_exercise_id} ───────────────────────


@router.delete(
    "/{workout_exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove exercise from workout",
    description=(
        "Deletes the WorkoutExercise and cascades to its WorkoutSet rows. "
        "Returns HTTP 403 if the exercise exists but belongs to another user."
    ),
)
async def delete_workout_exercise(
    workout_exercise_id: UUID,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    exercise_repo: Annotated[
        WorkoutExerciseRepository, Depends(get_workout_exercise_repository)
    ],
) -> None:
    cid = _correlation_id(request)

    record = await exercise_repo.get_by_id(workout_exercise_id)
    if record is None:
        _raise_not_found(cid)
    assert record is not None
    if record.user_id != current_user.id:
        _raise_forbidden(cid)

    await exercise_repo.delete(workout_exercise_id)
    logger.info(
        "WorkoutExercise deleted",
        extra={
            "user_id": str(current_user.id),
            "workout_exercise_id": str(workout_exercise_id),
        },
    )
