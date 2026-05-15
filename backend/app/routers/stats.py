"""
stats.py
PRLifts Backend

User statistics endpoint. Returns pre-aggregated workout and PR counts for
the authenticated user's HomeScreen consistency card.

user_id is always taken from the JWT sub — never from the request body or URL.
All counts return 0 for new users with no history — never null, never 404.

See docs/SCHEMA.md — workout table, personal_record table.
See docs/ARCHITECTURE.md Decision 92 — weekly consistency metric.
See docs/api/openapi.yaml — /v1/stats path.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.auth import AuthenticatedUser, get_current_user
from app.repositories.stats_repository import StatsRepository, get_stats_repository
from app.schemas import StatsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["stats"])


def _correlation_id(request: Request) -> str:
    return str(getattr(request.state, "correlation_id", ""))


@router.get(
    "",
    response_model=StatsResponse,
    summary="Get user statistics",
    description=(
        "Returns aggregated workout and PR statistics for the authenticated user. "
        "weekly_count reflects the current Mon–Sun UTC window. "
        "All fields return 0 for new users — never null, never 404."
    ),
)
async def get_stats(
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    repo: Annotated[StatsRepository, Depends(get_stats_repository)],
) -> StatsResponse:
    record = await repo.get_stats(user_id=current_user.id)

    logger.info(
        "stats fetched",
        extra={
            "user_id": str(current_user.id),
            "weekly_count": record.weekly_count,
            "total_workouts": record.total_workouts,
        },
    )

    return StatsResponse(
        weekly_count=record.weekly_count,
        best_week=record.best_week,
        total_workouts=record.total_workouts,
        total_prs=record.total_prs,
    )
