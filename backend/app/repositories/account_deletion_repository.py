"""
account_deletion_repository.py
PRLifts Backend

Repository protocol for hard account deletion.

Each method maps to one explicit step in the cascade sequence defined in
ARCHITECTURE.md Decision 95. Explicit per-step methods (rather than one
monolithic delete) let the fake track deletion order so tests can assert
the FK-safe sequence.

See docs/SCHEMA.md for FK constraints that govern the ordering:
  - workout_set → workout_exercise → workout → user (all CASCADE)
  - job → user (CASCADE)
  - biometric_consent → user (ON DELETE RESTRICT — must be handled before user)
  - audit_log — no FK, survives user deletion
  - image_deletion_queue — no FK, populated before job rows are deleted

See docs/ARCHITECTURE.md Decision 95 — account hard delete.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID


@dataclass
class AccountDeletionCounts:
    """Summary of rows removed at each cascade step."""

    workout_sets: int = 0
    workouts: int = 0
    jobs: int = 0
    images_queued: int = 0


class AccountDeletionRepository(Protocol):
    """
    Explicit per-step cascade interface for hard account deletion.

    Callers must invoke methods in the FK-safe order below — the protocol
    does NOT enforce ordering; that responsibility lives in the router.

    Safe order:
      1. get_generated_image_urls  — collect before jobs deleted
      2. enqueue_image_deletions   — queue URLs before jobs deleted
      3. delete_workout_sets       — before workouts (explicit for auditability)
      4. delete_workouts           — cascades workout_exercise rows
      5. delete_jobs               — clears job table
      6. set_biometric_consent_deleted — REQUIRED before delete_user_profile
                                         (ON DELETE RESTRICT)
      7. delete_user_profile       — removes user row; DB cascades remaining
                                     tables (personal_record, ai_request_log,
                                     sync_event_log, support_report)
      8. write_audit_log           — recorded after deletion completes
    """

    async def get_generated_image_urls(self, user_id: UUID) -> list[str]:
        """
        Returns image URLs from completed future_self job results.

        Reads job.result JSONB for all future_self jobs for this user where
        result->>'image_url' is not null.
        """
        ...

    async def enqueue_image_deletions(self, user_id: UUID, urls: list[str]) -> None:
        """Inserts each URL into image_deletion_queue for manual cleanup."""
        ...

    async def delete_workout_sets(self, user_id: UUID) -> int:
        """
        Explicitly deletes all workout_set rows owned by the user.

        Joins via workout_exercise → workout → user_id for the WHERE clause.
        Returns the number of rows deleted.
        """
        ...

    async def delete_workouts(self, user_id: UUID) -> int:
        """
        Deletes all workout rows for the user.

        workout_exercise rows cascade automatically (ON DELETE CASCADE on
        workout_id FK). Returns the number of workout rows deleted.
        """
        ...

    async def delete_jobs(self, user_id: UUID) -> int:
        """Deletes all job rows for the user. Returns row count."""
        ...

    async def set_biometric_consent_deleted(self, user_id: UUID) -> None:
        """
        Sets user_deleted_at = NOW() on all biometric_consent rows.

        Must be called before delete_user_profile — the FK is ON DELETE RESTRICT
        and will block user row deletion if any biometric_consent row exists.
        No-op when the user has no biometric_consent rows.
        """
        ...

    async def delete_user_profile(self, user_id: UUID) -> None:
        """
        Deletes the user row from the user table.

        PostgreSQL CASCADE handles remaining user-owned tables:
          personal_record, ai_request_log, sync_event_log, support_report,
          device_token, user_notification_preference.
        """
        ...

    async def write_audit_log(
        self, event_type: str, user_id: UUID, payload: dict[str, Any]
    ) -> None:
        """
        Appends a row to audit_log.

        audit_log has no FK on user_id — this write survives user deletion.
        Must be called AFTER delete_user_profile so the entry records confirmed
        completion.
        """
        ...


class SupabaseAdminClient(Protocol):
    """
    Interface for Supabase service-role operations that require admin credentials.

    The real implementation calls DELETE /auth/v1/admin/users/{user_id} using
    SUPABASE_SERVICE_ROLE_KEY. Tests inject a fake that records calls.
    """

    async def delete_auth_user(self, user_id: UUID) -> None:
        """
        Deletes the Supabase auth.users record for the given user_id.

        Must be called after all app-level data is deleted.
        """
        ...


@dataclass
class FakeAccountDeletionRepository:
    """
    In-memory AccountDeletionRepository for unit tests.

    Tracks the order of all deletion operations so tests can assert the
    FK-safe sequence was followed.
    """

    workout_sets: dict[UUID, list[object]] = field(default_factory=dict)
    workouts: dict[UUID, list[object]] = field(default_factory=dict)
    jobs: dict[UUID, list[object]] = field(default_factory=dict)
    user_profiles: set[UUID] = field(default_factory=set)
    image_deletion_queue: list[str] = field(default_factory=list)
    audit_log: list[dict[str, Any]] = field(default_factory=list)
    biometric_consent_deleted: set[UUID] = field(default_factory=set)
    deletion_order: list[str] = field(default_factory=list)

    async def get_generated_image_urls(self, user_id: UUID) -> list[str]:
        self.deletion_order.append("get_generated_image_urls")
        stored = self.jobs.get(user_id, [])
        urls = []
        for item in stored:
            if isinstance(item, dict) and item.get("job_type") == "future_self":
                result = item.get("result") or {}
                if isinstance(result, dict) and result.get("image_url"):
                    urls.append(result["image_url"])
        return urls

    async def enqueue_image_deletions(self, user_id: UUID, urls: list[str]) -> None:
        self.deletion_order.append("enqueue_image_deletions")
        self.image_deletion_queue.extend(urls)

    async def delete_workout_sets(self, user_id: UUID) -> int:
        self.deletion_order.append("delete_workout_sets")
        sets = self.workout_sets.pop(user_id, [])
        return len(sets)

    async def delete_workouts(self, user_id: UUID) -> int:
        self.deletion_order.append("delete_workouts")
        rows = self.workouts.pop(user_id, [])
        return len(rows)

    async def delete_jobs(self, user_id: UUID) -> int:
        self.deletion_order.append("delete_jobs")
        rows = self.jobs.pop(user_id, [])
        return len(rows)

    async def set_biometric_consent_deleted(self, user_id: UUID) -> None:
        self.deletion_order.append("set_biometric_consent_deleted")
        self.biometric_consent_deleted.add(user_id)

    async def delete_user_profile(self, user_id: UUID) -> None:
        self.deletion_order.append("delete_user_profile")
        self.user_profiles.discard(user_id)

    async def write_audit_log(
        self, event_type: str, user_id: UUID, payload: dict[str, Any]
    ) -> None:
        self.deletion_order.append("write_audit_log")
        self.audit_log.append(
            {"event_type": event_type, "user_id": user_id, "payload": payload}
        )


@dataclass
class FakeSupabaseAdminClient:
    """In-memory SupabaseAdminClient for unit tests."""

    deleted_user_ids: list[UUID] = field(default_factory=list)

    async def delete_auth_user(self, user_id: UUID) -> None:
        self.deleted_user_ids.append(user_id)


async def get_account_deletion_repository() -> AccountDeletionRepository:
    """
    FastAPI dependency marker for AccountDeletionRepository.

    Override in tests:
        app.dependency_overrides[get_account_deletion_repository] = (
            lambda: FakeAccountDeletionRepository(...)
        )

    Raises:
        RuntimeError: Always — must be overridden before any request is served.
    """
    raise RuntimeError(
        "get_account_deletion_repository has no default implementation. "
        "Wire a real implementation in main.py or override in tests."
    )


async def get_supabase_admin_client() -> SupabaseAdminClient:
    """
    FastAPI dependency marker for SupabaseAdminClient.

    Override in tests:
        app.dependency_overrides[get_supabase_admin_client] = (
            lambda: FakeSupabaseAdminClient()
        )

    Raises:
        RuntimeError: Always — must be overridden before any request is served.
    """
    raise RuntimeError(
        "get_supabase_admin_client has no default implementation. "
        "Wire a real implementation in main.py or override in tests."
    )
