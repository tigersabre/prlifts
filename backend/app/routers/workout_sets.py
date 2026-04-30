"""
workout_sets.py
PRLifts Backend

WorkoutSet CRUD endpoints with synchronous PR detection (Decision 88).

POST   /v1/workout-sets          — log a set, triggers PR detection
PATCH  /v1/workout-sets/{id}     — update a set, triggers PR recalculation
DELETE /v1/workout-sets/{id}     — delete a set, triggers PR recalculation

PR recalculation scans ALL historical sets for the (user, exercise, weight_modifier)
combination on every mutation (Decision 87). Uses the WorkoutExerciseRepository
for IDOR ownership chain verification on POST.

See docs/SCHEMA.md — workout_set, personal_record tables.
See docs/TEST_ENV_SETUP.md — PR Recalculation Acceptance Criteria.
See docs/api/openapi.yaml — /v1/workout-sets paths.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import AuthenticatedUser, get_current_user
from app.repositories.personal_record_repository import (
    PersonalRecordRepository,
    get_personal_record_repository,
)
from app.repositories.workout_exercise_repository import (
    WorkoutExerciseRepository,
    get_workout_exercise_repository,
)
from app.repositories.workout_set_repository import (
    WorkoutSetRecord,
    WorkoutSetRepository,
    get_workout_set_repository,
)
from app.schemas import (
    CreateWorkoutSetRequest,
    ErrorResponse,
    UpdateWorkoutSetRequest,
    WorkoutSetResponse,
)
from app.services.pr_service import recalculate_prs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workout-sets", tags=["workout-sets"])


def _correlation_id(request: Request) -> str:
    return str(getattr(request.state, "correlation_id", ""))


def _set_record_to_response(
    record: WorkoutSetRecord, is_personal_record: bool = False
) -> WorkoutSetResponse:
    response = WorkoutSetResponse.model_validate(record, from_attributes=True)
    return response.model_copy(update={"is_personal_record": is_personal_record})


def _raise_exercise_not_found(correlation_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorResponse(
            error_code="workout_exercise_not_found",
            message="Workout exercise not found.",
            request_id=correlation_id,
        ).model_dump(),
    )


def _raise_exercise_forbidden(correlation_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=ErrorResponse(
            error_code="workout_exercise_forbidden",
            message="You do not have access to this workout exercise.",
            request_id=correlation_id,
        ).model_dump(),
    )


def _raise_set_not_found(correlation_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorResponse(
            error_code="workout_set_not_found",
            message="Workout set not found.",
            request_id=correlation_id,
        ).model_dump(),
    )


def _raise_set_forbidden(correlation_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=ErrorResponse(
            error_code="workout_set_forbidden",
            message="You do not have access to this workout set.",
            request_id=correlation_id,
        ).model_dump(),
    )


# ── POST /v1/workout-sets ─────────────────────────────────────────────────────


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=WorkoutSetResponse,
    summary="Log a workout set",
    description=(
        "Records a set within a workout exercise. "
        "PR detection runs synchronously and is_personal_record is set in the "
        "response. The workout exercise must belong to the authenticated user."
    ),
)
async def create_workout_set(
    body: CreateWorkoutSetRequest,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    exercise_repo: Annotated[
        WorkoutExerciseRepository, Depends(get_workout_exercise_repository)
    ],
    set_repo: Annotated[WorkoutSetRepository, Depends(get_workout_set_repository)],
    pr_repo: Annotated[
        PersonalRecordRepository, Depends(get_personal_record_repository)
    ],
) -> WorkoutSetResponse:
    cid = _correlation_id(request)

    workout_exercise = await exercise_repo.get_by_id(body.workout_exercise_id)
    if workout_exercise is None:
        _raise_exercise_not_found(cid)
    assert workout_exercise is not None
    if workout_exercise.user_id != current_user.id:
        _raise_exercise_forbidden(cid)

    record = await set_repo.create(
        workout_exercise_id=body.workout_exercise_id,
        user_id=current_user.id,
        exercise_id=workout_exercise.exercise_id,
        set_number=body.set_number,
        set_type=body.set_type.value,
        weight=body.weight,
        weight_unit=body.weight_unit.value if body.weight_unit else None,
        weight_modifier=body.weight_modifier.value,
        modifier_value=body.modifier_value,
        modifier_unit=body.modifier_unit.value if body.modifier_unit else None,
        reps=body.reps,
        duration_seconds=body.duration_seconds,
        distance_meters=body.distance_meters,
        calories=body.calories,
        rpe=body.rpe,
        is_completed=body.is_completed,
        notes=body.notes,
    )

    all_sets = await set_repo.list_for_exercise_user(
        exercise_id=record.exercise_id,
        user_id=record.user_id,
        weight_modifier=record.weight_modifier,
    )
    is_pr = await recalculate_prs(
        user_id=record.user_id,
        exercise_id=record.exercise_id,
        weight_modifier=record.weight_modifier,
        current_set_id=record.id,
        sets=all_sets,
        pr_repo=pr_repo,
    )

    logger.info(
        "WorkoutSet created",
        extra={
            "user_id": str(current_user.id),
            "workout_set_id": str(record.id),
            "is_personal_record": is_pr,
        },
    )
    return _set_record_to_response(record, is_pr)


# ── PATCH /v1/workout-sets/{workout_set_id} ───────────────────────────────────


@router.patch(
    "/{workout_set_id}",
    response_model=WorkoutSetResponse,
    summary="Update a workout set",
    description=(
        "Partially updates the set. PR recalculation runs across all historical "
        "sets for the exercise. If weight_modifier changes, both the old and new "
        "modifier buckets are recalculated."
    ),
)
async def update_workout_set(
    workout_set_id: UUID,
    body: UpdateWorkoutSetRequest,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    set_repo: Annotated[WorkoutSetRepository, Depends(get_workout_set_repository)],
    pr_repo: Annotated[
        PersonalRecordRepository, Depends(get_personal_record_repository)
    ],
) -> WorkoutSetResponse:
    cid = _correlation_id(request)

    record = await set_repo.get_by_id(workout_set_id)
    if record is None:
        _raise_set_not_found(cid)
    assert record is not None
    if record.user_id != current_user.id:
        _raise_set_forbidden(cid)

    old_modifier = record.weight_modifier

    updates: dict[str, object] = {}
    for field in body.model_fields_set:
        value = getattr(body, field)
        updates[field] = value.value if hasattr(value, "value") else value

    if updates:
        updated = await set_repo.update(workout_set_id, updates)
        assert updated is not None
    else:
        updated = record

    new_modifier = updated.weight_modifier

    if old_modifier != new_modifier:
        old_sets = await set_repo.list_for_exercise_user(
            updated.exercise_id, updated.user_id, old_modifier
        )
        await recalculate_prs(
            user_id=updated.user_id,
            exercise_id=updated.exercise_id,
            weight_modifier=old_modifier,
            current_set_id=None,
            sets=old_sets,
            pr_repo=pr_repo,
        )
        new_sets = await set_repo.list_for_exercise_user(
            updated.exercise_id, updated.user_id, new_modifier
        )
        is_pr = await recalculate_prs(
            user_id=updated.user_id,
            exercise_id=updated.exercise_id,
            weight_modifier=new_modifier,
            current_set_id=updated.id,
            sets=new_sets,
            pr_repo=pr_repo,
        )
    else:
        all_sets = await set_repo.list_for_exercise_user(
            updated.exercise_id, updated.user_id, new_modifier
        )
        is_pr = await recalculate_prs(
            user_id=updated.user_id,
            exercise_id=updated.exercise_id,
            weight_modifier=new_modifier,
            current_set_id=updated.id,
            sets=all_sets,
            pr_repo=pr_repo,
        )

    logger.info(
        "WorkoutSet updated",
        extra={
            "user_id": str(current_user.id),
            "workout_set_id": str(workout_set_id),
            "is_personal_record": is_pr,
        },
    )
    return _set_record_to_response(updated, is_pr)


# ── DELETE /v1/workout-sets/{workout_set_id} ──────────────────────────────────


@router.delete(
    "/{workout_set_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workout set",
    description=(
        "Deletes the set and recalculates PRs. If the deleted set held the PR, "
        "the next best historical set is promoted."
    ),
)
async def delete_workout_set(
    workout_set_id: UUID,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    set_repo: Annotated[WorkoutSetRepository, Depends(get_workout_set_repository)],
    pr_repo: Annotated[
        PersonalRecordRepository, Depends(get_personal_record_repository)
    ],
) -> None:
    cid = _correlation_id(request)

    record = await set_repo.get_by_id(workout_set_id)
    if record is None:
        _raise_set_not_found(cid)
    assert record is not None
    if record.user_id != current_user.id:
        _raise_set_forbidden(cid)

    await set_repo.delete(workout_set_id)

    remaining = await set_repo.list_for_exercise_user(
        exercise_id=record.exercise_id,
        user_id=record.user_id,
        weight_modifier=record.weight_modifier,
    )
    await recalculate_prs(
        user_id=record.user_id,
        exercise_id=record.exercise_id,
        weight_modifier=record.weight_modifier,
        current_set_id=None,
        sets=remaining,
        pr_repo=pr_repo,
    )

    logger.info(
        "WorkoutSet deleted",
        extra={
            "user_id": str(current_user.id),
            "workout_set_id": str(workout_set_id),
        },
    )
