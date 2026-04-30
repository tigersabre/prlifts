"""
test_pr_detection.py
PRLifts Backend Tests

Unit tests for the PR detection and recalculation service.

Covers the six recalculation scenarios from docs/TEST_ENV_SETUP.md
§ PR Recalculation Acceptance Criteria:

  1. Edit set weight DOWN below current PR  → next best promoted
  2. Edit set weight UP above current PR    → new PR, previous_value preserved
  3. Edit non-PR set                        → no PersonalRecord changes
  4. Delete the current PR set             → next best promoted
  5. Delete the only set                   → PersonalRecord removed entirely
  6. Edit weight to EQUAL current PR       → no change (idempotent)

See docs/TEST_ENV_SETUP.md — PR Recalculation Acceptance Criteria.
See GitHub Issue #37 for acceptance criteria.
"""

import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("APP_VERSION", "0.1.0")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-supabase-jwt-secret-for-unit-tests")

from app.repositories.workout_set_repository import WorkoutSetRecord  # noqa: E402
from app.services.pr_service import (  # noqa: E402
    FakePersonalRecordRepository,
    recalculate_prs,
)

# ── Constants ────────────────────────────────────────────────────────────────

_USER = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_EXERCISE = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_WE = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_MODIFIER = "none"
_NOW = datetime(2026, 4, 29, 12, 0, 0, tzinfo=UTC)

# Short aliases for record_type strings used heavily in assertions
_W = "heaviest_weight"
_R = "most_reps"
_D = "longest_duration"
_DIS = "longest_distance"


def _set(
    weight: float | None = None,
    reps: int | None = None,
    duration_seconds: int | None = None,
    distance_meters: float | None = None,
    created_at: datetime | None = None,
    set_id: UUID | None = None,
) -> WorkoutSetRecord:
    return WorkoutSetRecord(
        id=set_id or uuid4(),
        workout_exercise_id=_WE,
        user_id=_USER,
        exercise_id=_EXERCISE,
        set_number=1,
        set_type="normal",
        weight=weight,
        weight_unit="kg" if weight is not None else None,
        weight_modifier=_MODIFIER,
        modifier_value=None,
        modifier_unit=None,
        reps=reps,
        duration_seconds=duration_seconds,
        distance_meters=distance_meters,
        calories=None,
        rpe=None,
        is_completed=True,
        notes=None,
        server_received_at=_NOW,
        created_at=created_at or _NOW,
        updated_at=_NOW,
    )


# ── Scenario 1: Edit PR set weight down — next best promoted ─────────────────


@pytest.mark.asyncio
async def test_scenario_1_edit_pr_weight_down_promotes_next_best() -> None:
    pr_repo = FakePersonalRecordRepository()
    set_a_id = uuid4()
    set_b_id = uuid4()

    set_b = _set(weight=95.0, set_id=set_b_id)

    # Establish set_a as current PR
    await pr_repo.upsert(
        _USER,
        _EXERCISE,
        set_a_id,
        _MODIFIER,
        "heaviest_weight",
        value=100.0,
        value_unit="kg",
        recorded_at=_NOW,
        previous_value=None,
        previous_recorded_at=None,
    )

    # Simulate editing set_a weight down to 90 — sets now has the updated set_a
    edited_set_a = _set(weight=90.0, set_id=set_a_id)
    sets_after = [edited_set_a, set_b]

    is_pr = await recalculate_prs(
        _USER,
        _EXERCISE,
        _MODIFIER,
        current_set_id=set_a_id,
        sets=sets_after,
        pr_repo=pr_repo,
    )

    pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _W)
    assert pr is not None
    assert pr.workout_set_id == set_b_id, "set_b (95kg) should be promoted as new PR"
    assert pr.value == 95.0
    assert pr.previous_value == 100.0, "previous_value should be the old PR value"
    assert is_pr is False, "set_a is not the current PR holder after the edit"


# ── Scenario 2: Edit set weight up above current PR — new PR created ──────────


@pytest.mark.asyncio
async def test_scenario_2_edit_weight_up_creates_new_pr() -> None:
    pr_repo = FakePersonalRecordRepository()
    set_a_id = uuid4()
    set_b_id = uuid4()

    set_a = _set(weight=100.0, set_id=set_a_id)

    await pr_repo.upsert(
        _USER,
        _EXERCISE,
        set_a_id,
        _MODIFIER,
        "heaviest_weight",
        value=100.0,
        value_unit="kg",
        recorded_at=_NOW,
        previous_value=None,
        previous_recorded_at=None,
    )

    # set_b edited from 80 to 110
    edited_set_b = _set(weight=110.0, set_id=set_b_id)
    sets_after = [set_a, edited_set_b]

    is_pr = await recalculate_prs(
        _USER,
        _EXERCISE,
        _MODIFIER,
        current_set_id=set_b_id,
        sets=sets_after,
        pr_repo=pr_repo,
    )

    pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _W)
    assert pr is not None
    assert pr.workout_set_id == set_b_id
    assert pr.value == 110.0
    assert pr.previous_value == 100.0, "previous_value should capture the beaten PR"
    assert is_pr is True


# ── Scenario 3: Edit non-PR set — no PersonalRecord changes ─────────────────


@pytest.mark.asyncio
async def test_scenario_3_edit_non_pr_set_no_changes() -> None:
    pr_repo = FakePersonalRecordRepository()
    set_a_id = uuid4()
    set_b_id = uuid4()

    set_a = _set(weight=100.0, set_id=set_a_id)

    await pr_repo.upsert(
        _USER,
        _EXERCISE,
        set_a_id,
        _MODIFIER,
        "heaviest_weight",
        value=100.0,
        value_unit="kg",
        recorded_at=_NOW,
        previous_value=None,
        previous_recorded_at=None,
    )

    original_pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _W)
    assert original_pr is not None
    original_updated_at = original_pr.updated_at

    # Editing set_b (not the PR) from 80 to 85
    edited_set_b = _set(weight=85.0, set_id=set_b_id)
    sets_after = [set_a, edited_set_b]

    is_pr = await recalculate_prs(
        _USER,
        _EXERCISE,
        _MODIFIER,
        current_set_id=set_b_id,
        sets=sets_after,
        pr_repo=pr_repo,
    )

    pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _W)
    assert pr is not None
    assert pr.workout_set_id == set_a_id, "PR holder must remain set_a"
    assert pr.value == 100.0
    assert pr.updated_at == original_updated_at, "updated_at must not change (no write)"
    assert is_pr is False


# ── Scenario 4: Delete current PR set — next best promoted ───────────────────


@pytest.mark.asyncio
async def test_scenario_4_delete_pr_set_promotes_next_best() -> None:
    pr_repo = FakePersonalRecordRepository()
    set_a_id = uuid4()
    set_b_id = uuid4()

    set_b = _set(weight=95.0, set_id=set_b_id)

    await pr_repo.upsert(
        _USER,
        _EXERCISE,
        set_a_id,
        _MODIFIER,
        "heaviest_weight",
        value=100.0,
        value_unit="kg",
        recorded_at=_NOW,
        previous_value=None,
        previous_recorded_at=None,
    )

    # Delete set_a — sets_after excludes it
    sets_after = [set_b]

    is_pr = await recalculate_prs(
        _USER,
        _EXERCISE,
        _MODIFIER,
        current_set_id=None,
        sets=sets_after,
        pr_repo=pr_repo,
    )

    pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _W)
    assert pr is not None
    assert pr.workout_set_id == set_b_id, "set_b should be promoted as new PR"
    assert pr.value == 95.0
    assert pr.previous_value == 100.0, "prev_value = old deleted PR"
    assert is_pr is False


# ── Scenario 5: Delete the only set — PR removed entirely ────────────────────


@pytest.mark.asyncio
async def test_scenario_5_delete_only_set_removes_pr() -> None:
    pr_repo = FakePersonalRecordRepository()
    set_a_id = uuid4()

    await pr_repo.upsert(
        _USER,
        _EXERCISE,
        set_a_id,
        _MODIFIER,
        "heaviest_weight",
        value=100.0,
        value_unit="kg",
        recorded_at=_NOW,
        previous_value=None,
        previous_recorded_at=None,
    )

    is_pr = await recalculate_prs(
        _USER,
        _EXERCISE,
        _MODIFIER,
        current_set_id=None,
        sets=[],  # no sets remaining
        pr_repo=pr_repo,
    )

    pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _W)
    assert pr is None, "PersonalRecord must be removed when no sets remain"
    assert is_pr is False


# ── Scenario 6: Edit weight to equal current PR — idempotent ─────────────────


@pytest.mark.asyncio
async def test_scenario_6_edit_to_equal_pr_no_change() -> None:
    pr_repo = FakePersonalRecordRepository()
    set_a_id = uuid4()
    set_b_id = uuid4()

    set_a = _set(weight=100.0, set_id=set_a_id)

    await pr_repo.upsert(
        _USER,
        _EXERCISE,
        set_a_id,
        _MODIFIER,
        "heaviest_weight",
        value=100.0,
        value_unit="kg",
        recorded_at=_NOW,
        previous_value=None,
        previous_recorded_at=None,
    )

    original_pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _W)
    assert original_pr is not None
    original_updated_at = original_pr.updated_at

    # set_b edited to exactly equal the current PR value
    edited_set_b = _set(weight=100.0, set_id=set_b_id)
    sets_after = [set_a, edited_set_b]

    is_pr = await recalculate_prs(
        _USER,
        _EXERCISE,
        _MODIFIER,
        current_set_id=set_b_id,
        sets=sets_after,
        pr_repo=pr_repo,
    )

    pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _W)
    assert pr is not None
    assert pr.workout_set_id == set_a_id, "tie: current PR holder preferred"
    assert pr.updated_at == original_updated_at, "no write should occur (idempotent)"
    assert is_pr is False, "set_b is not the PR holder"


# ── Multiple record types ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pr_tracked_per_record_type_independently() -> None:
    pr_repo = FakePersonalRecordRepository()
    weight_set = _set(weight=100.0)
    reps_set = _set(reps=20)
    both_set = _set(weight=80.0, reps=15)

    sets = [weight_set, reps_set, both_set]

    is_pr = await recalculate_prs(
        _USER,
        _EXERCISE,
        _MODIFIER,
        current_set_id=weight_set.id,
        sets=sets,
        pr_repo=pr_repo,
    )

    weight_pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _W)
    reps_pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _R)

    assert weight_pr is not None
    assert weight_pr.workout_set_id == weight_set.id
    assert reps_pr is not None
    assert reps_pr.workout_set_id == reps_set.id
    assert is_pr is True, "weight_set holds heaviest_weight PR"


@pytest.mark.asyncio
async def test_no_pr_created_when_no_matching_metric() -> None:
    pr_repo = FakePersonalRecordRepository()
    # Set has only reps — no weight
    reps_only = _set(reps=10)

    await recalculate_prs(
        _USER,
        _EXERCISE,
        _MODIFIER,
        current_set_id=reps_only.id,
        sets=[reps_only],
        pr_repo=pr_repo,
    )

    weight_pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _W)
    reps_pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _R)

    assert weight_pr is None, "No weight PR when no set has a weight value"
    assert reps_pr is not None
    assert reps_pr.value == 10.0


@pytest.mark.asyncio
async def test_is_pr_false_when_not_holding_any_pr() -> None:
    pr_repo = FakePersonalRecordRepository()
    set_a = _set(weight=100.0)
    set_b = _set(weight=80.0)

    is_pr = await recalculate_prs(
        _USER,
        _EXERCISE,
        _MODIFIER,
        current_set_id=set_b.id,  # set_b is NOT the best
        sets=[set_a, set_b],
        pr_repo=pr_repo,
    )

    assert is_pr is False


@pytest.mark.asyncio
async def test_first_set_always_creates_pr() -> None:
    pr_repo = FakePersonalRecordRepository()
    first_set = _set(weight=60.0, reps=10)

    is_pr = await recalculate_prs(
        _USER,
        _EXERCISE,
        _MODIFIER,
        current_set_id=first_set.id,
        sets=[first_set],
        pr_repo=pr_repo,
    )

    assert is_pr is True
    pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _W)
    assert pr is not None
    assert pr.previous_value is None, "No previous PR for first-ever set"


@pytest.mark.asyncio
async def test_duration_and_distance_prs_tracked() -> None:
    pr_repo = FakePersonalRecordRepository()
    s1 = _set(duration_seconds=3600)
    s2 = _set(distance_meters=5000.0)

    await recalculate_prs(
        _USER,
        _EXERCISE,
        _MODIFIER,
        current_set_id=s1.id,
        sets=[s1, s2],
        pr_repo=pr_repo,
    )

    dur_pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _D)
    dist_pr = await pr_repo.get_current_pr(_USER, _EXERCISE, _MODIFIER, _DIS)

    assert dur_pr is not None
    assert dur_pr.value == 3600.0
    assert dur_pr.value_unit == "seconds"
    assert dist_pr is not None
    assert dist_pr.value == 5000.0
    assert dist_pr.value_unit == "meters"
