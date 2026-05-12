"""
account.py
PRLifts Backend

Account management endpoint. Currently exposes hard account deletion.

POST /v1/account/delete — permanently delete the authenticated user's account.

The deletion is synchronous and completes within 30 seconds. Cascade order
follows FK constraints in docs/SCHEMA.md (sets → workouts → jobs →
image_deletion_queue → biometric_consent → user_profile → auth.users).

Fal.ai DPA is not yet signed: generated image URLs are written to
image_deletion_queue for manual operator cleanup rather than calling the
Fal.ai deletion API.

biometric_consent rows are retained for 1 year post-deletion (BIPA legal hold).
user_deleted_at is set before the user row is deleted so the ON DELETE RESTRICT
FK does not block deletion.

See docs/ARCHITECTURE.md Decision 95.
See docs/api/openapi.yaml — /v1/account/delete.
"""

import logging
import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.auth import AuthenticatedUser, get_current_user
from app.repositories.account_deletion_repository import (
    AccountDeletionRepository,
    SupabaseAdminClient,
    get_account_deletion_repository,
    get_supabase_admin_client,
)
from app.schemas import DeleteAccountRequest, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["account"])

_RATE_LIMIT_WINDOW_SECONDS = 3600
_RATE_LIMIT_MAX = 1


def _correlation_id(request: Request) -> str:
    return str(getattr(request.state, "correlation_id", ""))


async def _check_hourly_rate_limit(request: Request, user_id: str) -> None:
    """
    Enforces 1 request per user per hour for account deletion.

    Uses a Redis key account_delete:{user_id}:{hour} with TTL 3600.
    Fails open when Redis is unavailable — deletion is never blocked by a
    Redis failure. A separate, coarser rate-limit bucket from the general
    middleware (which uses 60-second windows) is required here because
    account deletion must be limited on an hourly basis.
    """
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        return

    hour = int(time.time()) // _RATE_LIMIT_WINDOW_SECONDS
    key = f"account_delete:{user_id}:{hour}"
    cid = _correlation_id(request)

    try:
        count: int = await redis.incr(key)
        if count == 1:
            await redis.expire(key, _RATE_LIMIT_WINDOW_SECONDS)
        if count > _RATE_LIMIT_MAX:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=ErrorResponse(
                    error_code="account_delete_rate_limited",
                    message="Account deletion may only be requested once per hour.",
                    request_id=cid,
                ).model_dump(),
                headers={"Retry-After": str(_RATE_LIMIT_WINDOW_SECONDS)},
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Account deletion rate-limit Redis failure",
            extra={"error": str(exc), "user_id": user_id},
        )


# ── POST /v1/account/delete ───────────────────────────────────────────────────


@router.post(
    "/delete",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete account",
    description=(
        "Permanently and irreversibly deletes the authenticated user's account "
        'and all associated data. Requires {"confirm": true} in the request body. '
        "Cascade order: workout_sets → workouts → jobs → image_deletion_queue → "
        "biometric_consent (user_deleted_at set) → user_profile → auth.users. "
        "Completes synchronously within 30 seconds. "
        "Rate limited to 1 request per user per hour."
    ),
)
async def delete_account(
    body: DeleteAccountRequest,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    repo: Annotated[
        AccountDeletionRepository, Depends(get_account_deletion_repository)
    ],
    supabase_admin: Annotated[SupabaseAdminClient, Depends(get_supabase_admin_client)],
) -> Response:
    cid = _correlation_id(request)
    user_id = current_user.id

    if not body.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="account_delete_not_confirmed",
                message="confirm must be true to delete your account.",
                request_id=cid,
            ).model_dump(),
        )

    await _check_hourly_rate_limit(request, str(user_id))

    # Step 1-2: collect and queue Fal.ai image URLs before job rows are deleted.
    image_urls = await repo.get_generated_image_urls(user_id)
    await repo.enqueue_image_deletions(user_id, image_urls)

    # Step 3-5: explicit cascade in FK-safe order.
    sets_deleted = await repo.delete_workout_sets(user_id)
    workouts_deleted = await repo.delete_workouts(user_id)
    jobs_deleted = await repo.delete_jobs(user_id)

    # Step 6: set user_deleted_at on biometric_consent rows BEFORE user deletion
    # (ON DELETE RESTRICT — will block the user row delete if skipped).
    await repo.set_biometric_consent_deleted(user_id)

    # Step 7: delete user row — remaining tables cascade automatically.
    await repo.delete_user_profile(user_id)

    # Step 8: audit log written after confirmed completion (no FK, survives deletion).
    audit_payload: dict[str, Any] = {
        "sets_deleted": sets_deleted,
        "workouts_deleted": workouts_deleted,
        "jobs_deleted": jobs_deleted,
        "images_queued": len(image_urls),
    }
    await repo.write_audit_log("user.deletion_completed", user_id, audit_payload)

    # Step 9: remove the Supabase auth identity last.
    await supabase_admin.delete_auth_user(user_id)

    logger.info(
        "Account deleted",
        extra={
            "user_id": str(user_id),
            "sets_deleted": sets_deleted,
            "workouts_deleted": workouts_deleted,
            "jobs_deleted": jobs_deleted,
            "images_queued": len(image_urls),
        },
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
