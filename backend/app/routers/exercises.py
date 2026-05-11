"""
exercises.py
PRLifts Backend

Exercise library endpoint. Returns exercises with optional full-text search and
attribute filters. Uses cursor-based pagination per ARCHITECTURE.md Decision 94.

GET /v1/exercises — list / search exercises (authenticated)

Empty results are always 200 with an empty data array, never 404.

See docs/SCHEMA.md — exercise table.
See docs/api/openapi.yaml — /v1/exercises paths.
"""

import base64
import logging
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth import AuthenticatedUser, get_current_user
from app.repositories.exercise_repository import (
    ExerciseRecord,
    ExerciseRepository,
    get_exercise_repository,
)
from app.schemas import (
    ErrorResponse,
    ExerciseListResponse,
    ExerciseResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exercises", tags=["exercises"])


def _correlation_id(request: Request) -> str:
    return str(getattr(request.state, "correlation_id", ""))


def _encode_cursor(created_at: datetime, record_id: UUID) -> str:
    """Encode a (created_at, id) keyset position as an opaque base64url string."""
    raw = f"{created_at.isoformat()}|{record_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    """
    Decode a cursor string back to (created_at, id).

    Raises ValueError for any malformed input so callers can return HTTP 400.
    """
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        ts_str, id_str = raw.split("|", 1)
        return datetime.fromisoformat(ts_str), UUID(id_str)
    except Exception as exc:
        raise ValueError(f"malformed cursor: {exc}") from exc


def _exercise_record_to_response(record: ExerciseRecord) -> ExerciseResponse:
    return ExerciseResponse.model_validate(record, from_attributes=True)


# ── GET /v1/exercises ─────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=ExerciseListResponse,
    summary="List and search exercises",
    description=(
        "Returns exercises from the shared library. "
        "When q is provided, results are filtered by trigram similarity and "
        "ordered by similarity DESC, created_at DESC, id DESC. "
        "When q is absent, results are ordered by created_at DESC, id DESC. "
        "Uses cursor-based pagination per ARCHITECTURE.md Decision 94. "
        "Empty results return HTTP 200 with an empty data array."
    ),
)
async def list_exercises(
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    repo: Annotated[ExerciseRepository, Depends(get_exercise_repository)],
    q: str | None = Query(default=None, description="Trigram search on exercise name"),
    muscle_group: str | None = Query(default=None),
    equipment: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=20),
    cursor: str | None = Query(default=None),
) -> ExerciseListResponse:
    cid = _correlation_id(request)

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="exercise_limit_invalid",
                message="limit must be between 1 and 100.",
                request_id=cid,
            ).model_dump(),
        )

    cursor_created_at: datetime | None = None
    cursor_id: UUID | None = None
    if cursor is not None:
        try:
            cursor_created_at, cursor_id = _decode_cursor(cursor)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code="exercise_cursor_invalid",
                    message="The provided cursor is invalid.",
                    request_id=cid,
                ).model_dump(),
            ) from exc

    records, has_more = await repo.list_exercises(
        q=q,
        muscle_group=muscle_group,
        equipment=equipment,
        category=category,
        limit=limit,
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id,
    )

    next_cursor: str | None = None
    if has_more and records:
        last = records[-1]
        next_cursor = _encode_cursor(last.created_at, last.id)

    logger.info(
        "Exercises listed",
        extra={
            "user_id": str(current_user.id),
            "q": q,
            "result_count": len(records),
        },
    )

    return ExerciseListResponse(
        data=[_exercise_record_to_response(r) for r in records],
        next_cursor=next_cursor,
        has_more=has_more,
    )
