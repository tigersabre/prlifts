"""
jobs.py
PRLifts Backend

Async AI job endpoints (V1: insight only).

POST /v1/jobs           — create an AI job, enqueue background task, return 202
GET  /v1/jobs/{job_id}  — poll job status; result populated when complete

All AI operations are asynchronous per docs/ARCHITECTURE.md Rule 7.
Clients receive a job_id immediately and poll with exponential backoff
(2 s initial, 10 s ceiling, 15 attempts max).

See docs/ARCHITECTURE.md — AI Operations Async Pattern.
See docs/JOB_CATALOG.md — job lifecycle and expiry.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from app.auth import AuthenticatedUser, get_current_user
from app.config import get_settings
from app.repositories.job_repository import (
    AIRequestLogRepository,
    JobRepository,
    PromptTemplateRepository,
    get_ai_request_log_repository,
    get_job_repository,
    get_prompt_template_repository,
)
from app.repositories.workout_repository import (
    WorkoutRepository,
    get_workout_repository,
)
from app.schemas import (
    CreateJobRequest,
    ErrorResponse,
    JobCreateResponse,
    JobStatusResponse,
    JobType,
)
from app.services.insight_service import (
    get_anthropic_client,
    load_forbidden_phrases,
    process_insight_job,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _correlation_id(request: Request) -> str:
    return str(getattr(request.state, "correlation_id", ""))


def _raise_job_not_found(correlation_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorResponse(
            error_code="job_not_found",
            message="Job not found.",
            request_id=correlation_id,
        ).model_dump(),
    )


def _raise_job_forbidden(correlation_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=ErrorResponse(
            error_code="job_forbidden",
            message="You do not have access to this job.",
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


def _raise_unsupported_job_type(correlation_id: str) -> None:
    raise HTTPException(
        status_code=422,
        detail=ErrorResponse(
            error_code="job_type_unsupported",
            message="Only 'insight' jobs are supported in this version.",
            request_id=correlation_id,
        ).model_dump(),
    )


# ── POST /v1/jobs ─────────────────────────────────────────────────────────────


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobCreateResponse,
    summary="Create an AI job",
    description=(
        "Creates an async AI job for the specified workout. "
        "V1 supports job_type 'insight' only. "
        "Returns HTTP 202 immediately with a job_id. "
        "Poll GET /v1/jobs/{job_id} to retrieve the result."
    ),
)
async def create_job(
    body: CreateJobRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    job_repo: Annotated[JobRepository, Depends(get_job_repository)],
    prompt_repo: Annotated[
        PromptTemplateRepository, Depends(get_prompt_template_repository)
    ],
    ai_log_repo: Annotated[
        AIRequestLogRepository, Depends(get_ai_request_log_repository)
    ],
    workout_repo: Annotated[WorkoutRepository, Depends(get_workout_repository)],
) -> JobCreateResponse:
    cid = _correlation_id(request)

    if body.job_type != JobType.insight:
        _raise_unsupported_job_type(cid)

    workout = await workout_repo.get_by_id(body.workout_id)
    if workout is None:
        _raise_workout_not_found(cid)
    assert workout is not None
    if workout.user_id != current_user.id:
        _raise_workout_forbidden(cid)

    job = await job_repo.create(
        user_id=current_user.id,
        job_type=body.job_type.value,
    )

    settings = get_settings()
    ai_client = get_anthropic_client(
        api_key=settings.claude_api_key,
        mocked=settings.ai_providers_mocked,
    )
    forbidden_phrases = load_forbidden_phrases()

    background_tasks.add_task(
        process_insight_job,
        job_id=job.id,
        user_id=current_user.id,
        workout_id=body.workout_id,
        job_repo=job_repo,
        prompt_repo=prompt_repo,
        ai_log_repo=ai_log_repo,
        ai_client=ai_client,
        forbidden_phrases=forbidden_phrases,
    )

    logger.info(
        "Insight job created",
        extra={
            "user_id": str(current_user.id),
            "job_id": str(job.id),
            "workout_id": str(body.workout_id),
        },
    )
    return JobCreateResponse(job_id=job.id)


# ── GET /v1/jobs/{job_id} ─────────────────────────────────────────────────────


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description=(
        "Returns the current status of an AI job. "
        "result is populated when status is 'complete'. "
        "error_message is set when status is 'failed' or 'expired'."
    ),
)
async def get_job(
    job_id: UUID,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    job_repo: Annotated[JobRepository, Depends(get_job_repository)],
) -> JobStatusResponse:
    cid = _correlation_id(request)

    job = await job_repo.get_by_id(job_id)
    if job is None:
        _raise_job_not_found(cid)
    assert job is not None
    if job.user_id != current_user.id:
        _raise_job_forbidden(cid)

    return JobStatusResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        result=job.result,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        expires_at=job.expires_at,
    )
