"""
test_repositories_integration.py
PRLifts Backend Tests

Integration tests for all 10 asyncpg repository concrete classes.
Each test creates its own data and cleans up on completion, so the
tests are order-independent and safe to run against any environment.

Skipped automatically when ENVIRONMENT=test (the CI default).
To run locally:

    ENVIRONMENT=development DATABASE_URL=<dsn> pytest \\
        tests/test_repositories_integration.py -v

See docs/ARCHITECTURE.md Decision 96 — direct asyncpg pool.
"""

import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import asyncpg
import pytest

_REAL_DB_AVAILABLE = os.environ.get("ENVIRONMENT") != "test"

_SKIP = pytest.mark.skipif(
    not _REAL_DB_AVAILABLE,
    reason=(
        "Integration test — requires a real PostgreSQL instance. "
        "Run with ENVIRONMENT=development and a valid DATABASE_URL."
    ),
)


# ── Pool fixture ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
async def pool() -> AsyncGenerator[asyncpg.Pool, None]:
    if not _REAL_DB_AVAILABLE:
        pytest.skip("No real DB available")
    from app.db import create_pool

    p = await create_pool(os.environ["DATABASE_URL"])
    yield p
    await p.close()


# ── UserRepository ────────────────────────────────────────────────────────────


@_SKIP
async def test_user_repo_create_get_exists_update(pool: asyncpg.Pool) -> None:
    from app.repositories.asyncpg_user_repository import AsyncpgUserRepository

    repo = AsyncpgUserRepository(pool)
    uid = uuid4()
    try:
        created = await repo.create(uid, "Int Test User", "lbs", "cm")
        assert created.id == uid
        assert created.display_name == "Int Test User"
        assert created.unit_preference == "lbs"
        assert created.measurement_unit == "cm"
        assert created.beta_tier == "none"

        fetched = await repo.get_by_id(uid)
        assert fetched is not None
        assert fetched.id == uid

        assert await repo.exists(uid) is True
        assert await repo.exists(uuid4()) is False

        updated = await repo.update(uid, {"display_name": "Updated Name"})
        assert updated is not None
        assert updated.display_name == "Updated Name"

        updated_enum = await repo.update(uid, {"unit_preference": "kg"})
        assert updated_enum is not None
        assert updated_enum.unit_preference == "kg"
    finally:
        await pool.execute('DELETE FROM "user" WHERE id = $1', uid)


# ── WorkoutRepository ─────────────────────────────────────────────────────────


@_SKIP
async def test_workout_repo_create_list_update_delete(pool: asyncpg.Pool) -> None:
    from app.repositories.asyncpg_user_repository import AsyncpgUserRepository
    from app.repositories.asyncpg_workout_repository import AsyncpgWorkoutRepository

    user_repo = AsyncpgUserRepository(pool)
    repo = AsyncpgWorkoutRepository(pool)
    uid = uuid4()
    try:
        await user_repo.create(uid, "WO Test User", "lbs", "cm")

        w = await repo.create(uid, "ad_hoc", "weightlifting", "Leg Day", "gym", None)
        assert w.user_id == uid
        assert w.status == "in_progress"
        assert w.type == "ad_hoc"
        assert w.format == "weightlifting"
        assert w.location == "gym"

        fetched = await repo.get_by_id(w.id)
        assert fetched is not None
        assert fetched.id == w.id

        page, has_more = await repo.list_for_user(uid, 10, None, None, None, None)
        assert len(page) == 1
        assert page[0].id == w.id
        assert has_more is False

        updated = await repo.update(w.id, {"status": "completed", "name": "Done"})
        assert updated is not None
        assert updated.status == "completed"
        assert updated.name == "Done"

        w2 = await repo.create(uid, "ad_hoc", "cardio", None, None, None)
        _, has_more2 = await repo.list_for_user(uid, 1, None, None, None, None)
        assert has_more2 is True

        deleted = await repo.delete(w2.id)
        assert deleted is True
        assert await repo.delete(w2.id) is False
    finally:
        await pool.execute('DELETE FROM "user" WHERE id = $1', uid)


# ── WorkoutExerciseRepository ─────────────────────────────────────────────────


@_SKIP
async def test_workout_exercise_repo_create_get_delete(pool: asyncpg.Pool) -> None:
    from app.repositories.asyncpg_user_repository import AsyncpgUserRepository
    from app.repositories.asyncpg_workout_exercise_repository import (
        AsyncpgWorkoutExerciseRepository,
    )
    from app.repositories.asyncpg_workout_repository import AsyncpgWorkoutRepository

    uid = uuid4()
    try:
        await AsyncpgUserRepository(pool).create(uid, "WE Test", "lbs", "cm")
        w = await AsyncpgWorkoutRepository(pool).create(
            uid, "ad_hoc", "weightlifting", None, None, None
        )

        ex_row = await pool.fetchrow(
            """
            INSERT INTO exercise (name, category, muscle_group, equipment, is_custom)
            VALUES ($1, 'strength', 'biceps', 'dumbbell', true)
            RETURNING *
            """,
            f"_int_we_{uuid4().hex[:8]}",
        )
        ex_id = ex_row["id"]

        repo = AsyncpgWorkoutExerciseRepository(pool)
        we = await repo.create(w.id, uid, ex_id, 0, "some notes", 90)
        assert we.workout_id == w.id
        assert we.user_id == uid
        assert we.exercise_id == ex_id
        assert we.order_index == 0
        assert we.notes == "some notes"
        assert we.rest_seconds == 90

        fetched = await repo.get_by_id(we.id)
        assert fetched is not None
        assert fetched.user_id == uid

        deleted = await repo.delete(we.id)
        assert deleted is True
        assert await repo.delete(we.id) is False
    finally:
        await pool.execute('DELETE FROM "user" WHERE id = $1', uid)
        await pool.execute("DELETE FROM exercise WHERE name LIKE '_int_we_%'")


# ── WorkoutSetRepository ──────────────────────────────────────────────────────


@_SKIP
async def test_workout_set_repo_create_get_update_list_delete(
    pool: asyncpg.Pool,
) -> None:
    from app.repositories.asyncpg_user_repository import AsyncpgUserRepository
    from app.repositories.asyncpg_workout_exercise_repository import (
        AsyncpgWorkoutExerciseRepository,
    )
    from app.repositories.asyncpg_workout_repository import AsyncpgWorkoutRepository
    from app.repositories.asyncpg_workout_set_repository import (
        AsyncpgWorkoutSetRepository,
    )

    uid = uuid4()
    try:
        await AsyncpgUserRepository(pool).create(uid, "WS Test", "lbs", "cm")
        w = await AsyncpgWorkoutRepository(pool).create(
            uid, "ad_hoc", "weightlifting", None, None, None
        )
        ex_row = await pool.fetchrow(
            """
            INSERT INTO exercise (name, category, muscle_group, equipment, is_custom)
            VALUES ($1, 'strength', 'mid_chest', 'barbell', true)
            RETURNING *
            """,
            f"_int_ws_{uuid4().hex[:8]}",
        )
        ex_id = ex_row["id"]
        we = await AsyncpgWorkoutExerciseRepository(pool).create(
            w.id, uid, ex_id, 0, None, None
        )

        repo = AsyncpgWorkoutSetRepository(pool)
        ws = await repo.create(
            we.id,
            uid,
            ex_id,
            1,
            "normal",
            100.0,
            "lbs",
            "none",
            None,
            None,
            5,
            None,
            None,
            None,
            8,
            True,
            None,
        )
        assert ws.workout_exercise_id == we.id
        assert ws.user_id == uid
        assert ws.exercise_id == ex_id
        assert ws.weight == 100.0
        assert ws.reps == 5
        assert ws.is_completed is True

        fetched = await repo.get_by_id(ws.id)
        assert fetched is not None
        assert fetched.user_id == uid

        updated = await repo.update(ws.id, {"reps": 8, "rpe": 7})
        assert updated is not None
        assert updated.reps == 8
        assert updated.rpe == 7

        history = await repo.list_for_exercise_user(ex_id, uid, "none")
        assert len(history) >= 1
        assert any(r.id == ws.id for r in history)

        assert await repo.delete(ws.id) is True
        assert await repo.delete(ws.id) is False
    finally:
        await pool.execute('DELETE FROM "user" WHERE id = $1', uid)
        await pool.execute("DELETE FROM exercise WHERE name LIKE '_int_ws_%'")


# ── PersonalRecordRepository ──────────────────────────────────────────────────


@_SKIP
async def test_personal_record_repo_upsert_get_delete(pool: asyncpg.Pool) -> None:
    from app.repositories.asyncpg_personal_record_repository import (
        AsyncpgPersonalRecordRepository,
    )
    from app.repositories.asyncpg_user_repository import AsyncpgUserRepository
    from app.repositories.asyncpg_workout_exercise_repository import (
        AsyncpgWorkoutExerciseRepository,
    )
    from app.repositories.asyncpg_workout_repository import AsyncpgWorkoutRepository
    from app.repositories.asyncpg_workout_set_repository import (
        AsyncpgWorkoutSetRepository,
    )

    uid = uuid4()
    try:
        await AsyncpgUserRepository(pool).create(uid, "PR Test", "lbs", "cm")
        w = await AsyncpgWorkoutRepository(pool).create(
            uid, "ad_hoc", "weightlifting", None, None, None
        )
        ex_row = await pool.fetchrow(
            """
            INSERT INTO exercise (name, category, muscle_group, equipment, is_custom)
            VALUES ($1, 'strength', 'mid_chest', 'barbell', true)
            RETURNING *
            """,
            f"_int_pr_{uuid4().hex[:8]}",
        )
        ex_id = ex_row["id"]
        we = await AsyncpgWorkoutExerciseRepository(pool).create(
            w.id, uid, ex_id, 0, None, None
        )
        ws = await AsyncpgWorkoutSetRepository(pool).create(
            we.id,
            uid,
            ex_id,
            1,
            "normal",
            100.0,
            "lbs",
            "none",
            None,
            None,
            5,
            None,
            None,
            None,
            None,
            True,
            None,
        )

        repo = AsyncpgPersonalRecordRepository(pool)
        now = datetime.now(UTC)

        no_pr = await repo.get_current_pr(uid, ex_id, "none", "heaviest_weight")
        assert no_pr is None

        pr = await repo.upsert(
            uid,
            ex_id,
            ws.id,
            "none",
            "heaviest_weight",
            100.0,
            "lbs",
            now,
            None,
            None,
        )
        assert pr.value == 100.0
        assert pr.previous_value is None

        fetched = await repo.get_current_pr(uid, ex_id, "none", "heaviest_weight")
        assert fetched is not None
        assert fetched.id == pr.id

        ws2 = await AsyncpgWorkoutSetRepository(pool).create(
            we.id,
            uid,
            ex_id,
            2,
            "normal",
            110.0,
            "lbs",
            "none",
            None,
            None,
            5,
            None,
            None,
            None,
            None,
            True,
            None,
        )
        pr2 = await repo.upsert(
            uid,
            ex_id,
            ws2.id,
            "none",
            "heaviest_weight",
            110.0,
            "lbs",
            now + timedelta(days=7),
            100.0,
            now,
        )
        assert pr2.value == 110.0
        assert pr2.previous_value == 100.0
        assert pr2.id == pr.id  # same row, updated

        deleted = await repo.delete_if_exists(uid, ex_id, "none", "heaviest_weight")
        assert deleted is True
        second = await repo.delete_if_exists(uid, ex_id, "none", "heaviest_weight")
        assert second is False
    finally:
        await pool.execute('DELETE FROM "user" WHERE id = $1', uid)
        await pool.execute("DELETE FROM exercise WHERE name LIKE '_int_pr_%'")


# ── ExerciseRepository ────────────────────────────────────────────────────────


@_SKIP
async def test_exercise_repo_list_and_search(pool: asyncpg.Pool) -> None:
    from app.repositories.asyncpg_exercise_repository import AsyncpgExerciseRepository

    repo = AsyncpgExerciseRepository(pool)

    page, _ = await repo.list_exercises(None, None, None, None, 10, None, None)
    assert isinstance(page, list)
    if page:
        rec = page[0]
        assert rec.id is not None
        assert isinstance(rec.secondary_muscle_groups, list)

    results, _ = await repo.list_exercises("bench", None, None, None, 10, None, None)
    assert isinstance(results, list)


# ── StatsRepository ───────────────────────────────────────────────────────────


@_SKIP
async def test_stats_repo_returns_zeroes_for_new_user(pool: asyncpg.Pool) -> None:
    from app.repositories.asyncpg_stats_repository import AsyncpgStatsRepository
    from app.repositories.asyncpg_user_repository import AsyncpgUserRepository

    uid = uuid4()
    try:
        await AsyncpgUserRepository(pool).create(uid, "Stats Test", "lbs", "cm")
        repo = AsyncpgStatsRepository(pool)
        stats = await repo.get_stats(uid)
        assert stats.weekly_count == 0
        assert stats.best_week == 0
        assert stats.total_workouts == 0
        assert stats.total_prs == 0
    finally:
        await pool.execute('DELETE FROM "user" WHERE id = $1', uid)


# ── JobRepository ─────────────────────────────────────────────────────────────


@_SKIP
async def test_job_repo_create_get_update_expire_stale(pool: asyncpg.Pool) -> None:
    from app.repositories.asyncpg_job_repository import AsyncpgJobRepository
    from app.repositories.asyncpg_user_repository import AsyncpgUserRepository

    uid = uuid4()
    try:
        await AsyncpgUserRepository(pool).create(uid, "Job Test", "lbs", "cm")
        repo = AsyncpgJobRepository(pool)

        job = await repo.create(uid, "insight")
        assert job.user_id == uid
        assert job.job_type == "insight"
        assert job.status == "pending"
        assert job.result is None

        fetched = await repo.get_by_id(job.id)
        assert fetched is not None
        assert fetched.id == job.id

        await repo.update(job.id, {"status": "processing"})
        updated = await repo.get_by_id(job.id)
        assert updated is not None
        assert updated.status == "processing"

        await repo.update(
            job.id,
            {
                "status": "complete",
                "result": {"insight": "Good work!"},
                "completed_at": datetime.now(UTC),
            },
        )
        completed = await repo.get_by_id(job.id)
        assert completed is not None
        assert completed.status == "complete"
        assert completed.result == {"insight": "Good work!"}

        stale_job = await repo.create(uid, "insight")
        await pool.execute(
            "UPDATE job SET expires_at = NOW() - INTERVAL '1 minute' WHERE id = $1",
            stale_job.id,
        )
        count = await repo.expire_stale(datetime.now(UTC))
        assert count >= 1

        expired = await repo.get_by_id(stale_job.id)
        assert expired is not None
        assert expired.status == "expired"
    finally:
        await pool.execute('DELETE FROM "user" WHERE id = $1', uid)


# ── PromptTemplateRepository ──────────────────────────────────────────────────


@_SKIP
async def test_prompt_template_repo_get_active(pool: asyncpg.Pool) -> None:
    from app.repositories.asyncpg_job_repository import AsyncpgPromptTemplateRepository

    repo = AsyncpgPromptTemplateRepository(pool)
    result = await repo.get_active("insight")
    if result is not None:
        assert result.feature == "insight"
        assert result.is_active is True
        assert result.prompt_text != ""


# ── AIRequestLogRepository ────────────────────────────────────────────────────


@_SKIP
async def test_ai_request_log_repo_create(pool: asyncpg.Pool) -> None:
    from app.repositories.asyncpg_job_repository import (
        AsyncpgAIRequestLogRepository,
        AsyncpgJobRepository,
    )
    from app.repositories.asyncpg_user_repository import AsyncpgUserRepository

    uid = uuid4()
    try:
        await AsyncpgUserRepository(pool).create(uid, "AILog Test", "lbs", "cm")
        job = await AsyncpgJobRepository(pool).create(uid, "insight")

        repo = AsyncpgAIRequestLogRepository(pool)
        log = await repo.create(
            user_id=uid,
            prompt_template_id=None,
            job_id=job.id,
            endpoint="/v1/jobs/insights",
            model="claude-sonnet-4-6",
            response="Great work on those sets!",
            duration_ms=1234,
            quality_score=None,
        )
        assert log.user_id == uid
        assert log.job_id == job.id
        assert log.model == "claude-sonnet-4-6"
        assert log.duration_ms == 1234
        assert log.response == "Great work on those sets!"
        assert log.quality_score is None
        assert log.expires_at > datetime.now(UTC)
    finally:
        await pool.execute('DELETE FROM "user" WHERE id = $1', uid)
