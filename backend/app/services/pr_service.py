"""
pr_service.py
PRLifts Backend

Personal Record detection and recalculation service (Decision 87, Decision 88).

PR detection runs synchronously on every WorkoutSet create, update, and delete.
PR recalculation scans ALL historical sets for the affected (user, exercise,
weight_modifier) combination — not just the current workout.

PRs are tracked separately per weight_modifier: a bodyweight squat PR and a
weighted-vest squat PR are independent records for the same exercise.

The six recalculation scenarios from docs/TEST_ENV_SETUP.md § PR Recalculation
Acceptance Criteria are handled by recalculate_prs.

See docs/SCHEMA.md — personal_record table.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.repositories.personal_record_repository import (
    PersonalRecordRecord,
    PersonalRecordRepository,
)
from app.repositories.workout_set_repository import WorkoutSetRecord

# Maps record_type → attribute name on WorkoutSetRecord
_RECORD_TYPE_ATTRS: dict[str, str] = {
    "heaviest_weight": "weight",
    "most_reps": "reps",
    "longest_duration": "duration_seconds",
    "longest_distance": "distance_meters",
}


def _value_unit(set_record: WorkoutSetRecord, record_type: str) -> str | None:
    if record_type == "heaviest_weight":
        return set_record.weight_unit
    if record_type == "most_reps":
        return "reps"
    if record_type == "longest_duration":
        return "seconds"
    if record_type == "longest_distance":
        return "meters"
    return None


def _find_best_set(
    sets: list[WorkoutSetRecord],
    attr: str,
    current_pr_set_id: UUID | None,
) -> WorkoutSetRecord | None:
    """
    Returns the set holding the best value for the given attribute.

    Tie-breaking: prefer the current PR holder (idempotent — scenario 6),
    then fall back to the set with the earliest created_at for stability.
    """
    candidates = [s for s in sets if getattr(s, attr) is not None]
    if not candidates:
        return None

    max_val = max(getattr(s, attr) for s in candidates)
    tied = [s for s in candidates if getattr(s, attr) == max_val]

    if len(tied) == 1:
        return tied[0]

    if current_pr_set_id is not None:
        for s in tied:
            if s.id == current_pr_set_id:
                return s

    return min(tied, key=lambda s: s.created_at)


async def recalculate_prs(
    user_id: UUID,
    exercise_id: UUID,
    weight_modifier: str,
    current_set_id: UUID | None,
    sets: list[WorkoutSetRecord],
    pr_repo: PersonalRecordRepository,
) -> bool:
    """
    Recalculates personal records for all record types given the full set history.

    Handles all six scenarios from docs/TEST_ENV_SETUP.md § PR Recalculation:
      1. Edit PR set weight down — new holder promoted from history
      2. Edit set weight up above current PR — new PR, previous_value preserved
      3. Edit non-PR set — no change (idempotent)
      4. Delete current PR set — next best promoted
      5. Delete only set — PR removed entirely
      6. Edit to equal current PR — no change (idempotent)

    Args:
        user_id: The user who owns the sets.
        exercise_id: The exercise being tracked.
        weight_modifier: Modifier bucket (none / assisted / weighted).
        current_set_id: The set just created or updated (None for delete).
        sets: All sets for (user_id, exercise_id, weight_modifier) AFTER the
              mutation — the deleted set must already be absent.
        pr_repo: PersonalRecord persistence.

    Returns:
        True if current_set_id holds any personal record after recalculation.
    """
    is_pr = False

    for record_type, attr in _RECORD_TYPE_ATTRS.items():
        current_pr = await pr_repo.get_current_pr(
            user_id, exercise_id, weight_modifier, record_type
        )
        current_pr_set_id = current_pr.workout_set_id if current_pr else None

        best = _find_best_set(sets, attr, current_pr_set_id)

        if best is None:
            # Scenario 5: no sets left — remove PR if it existed
            if current_pr is not None:
                await pr_repo.delete_if_exists(
                    user_id, exercise_id, weight_modifier, record_type
                )
            continue

        best_val = float(getattr(best, attr))

        # Scenarios 3 & 6: same holder, same value → no write needed
        if (
            current_pr is not None
            and best.id == current_pr.workout_set_id
            and best_val == float(current_pr.value)
        ):
            if current_set_id == best.id:
                is_pr = True
            continue

        # Determine previous_value for the upsert
        if current_pr is not None and best.id != current_pr.workout_set_id:
            # PR holder changing (scenarios 1, 2, 4): prev = old PR value
            prev_val: float | None = float(current_pr.value)
            prev_at: datetime | None = current_pr.recorded_at
        elif current_pr is not None:
            # Same holder, value changed (e.g., edited): preserve the chain
            prev_val = current_pr.previous_value
            prev_at = current_pr.previous_recorded_at
        else:
            # First PR ever for this combination
            prev_val = None
            prev_at = None

        await pr_repo.upsert(
            user_id=user_id,
            exercise_id=exercise_id,
            workout_set_id=best.id,
            weight_modifier=weight_modifier,
            record_type=record_type,
            value=best_val,
            value_unit=_value_unit(best, record_type),
            recorded_at=best.created_at,
            previous_value=prev_val,
            previous_recorded_at=prev_at,
        )

        if current_set_id == best.id:
            is_pr = True

    return is_pr


class FakePersonalRecordRepository:
    """
    In-memory PersonalRecordRepository for unit tests.
    Keyed by (user_id, exercise_id, weight_modifier, record_type).
    """

    def __init__(self) -> None:
        self._store: dict[tuple[UUID, UUID, str, str], PersonalRecordRecord] = {}

    async def get_current_pr(
        self,
        user_id: UUID,
        exercise_id: UUID,
        weight_modifier: str,
        record_type: str,
    ) -> PersonalRecordRecord | None:
        return self._store.get((user_id, exercise_id, weight_modifier, record_type))

    async def upsert(
        self,
        user_id: UUID,
        exercise_id: UUID,
        workout_set_id: UUID,
        weight_modifier: str,
        record_type: str,
        value: float,
        value_unit: str | None,
        recorded_at: datetime,
        previous_value: float | None,
        previous_recorded_at: datetime | None,
    ) -> PersonalRecordRecord:
        key = (user_id, exercise_id, weight_modifier, record_type)
        now = datetime.now(UTC)
        existing = self._store.get(key)
        record = PersonalRecordRecord(
            id=existing.id if existing else uuid4(),
            user_id=user_id,
            exercise_id=exercise_id,
            workout_set_id=workout_set_id,
            weight_modifier=weight_modifier,
            record_type=record_type,
            value=value,
            value_unit=value_unit,
            recorded_at=recorded_at,
            previous_value=previous_value,
            previous_recorded_at=previous_recorded_at,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self._store[key] = record
        return record

    async def delete_if_exists(
        self,
        user_id: UUID,
        exercise_id: UUID,
        weight_modifier: str,
        record_type: str,
    ) -> bool:
        key = (user_id, exercise_id, weight_modifier, record_type)
        if key in self._store:
            del self._store[key]
            return True
        return False
