"""
test_exercises.py
PRLifts Backend Tests

Unit tests for GET /v1/exercises — exercise library search and list endpoint.

Coverage:
  - Text search (q parameter)
  - muscle_group filter
  - Combined search + filter
  - Empty results (always 200, never 404)
  - Cursor-based pagination (Decision 94)
  - limit boundary validation
  - Invalid cursor → 400
  - GIN index usage assertion (real-DB integration test, skipped in unit mode)

See docs/SCHEMA.md — exercise table.
See docs/ARCHITECTURE.md Decision 94 — cursor-based pagination.
"""

import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from app.repositories.exercise_repository import ExerciseRecord

# ── Constants ────────────────────────────────────────────────────────────────

_SECRET: str = os.environ.get(
    "SUPABASE_JWT_SECRET", "test-supabase-jwt-secret-for-unit-tests"
)
_ALGORITHM = "HS256"
_AUDIENCE = "authenticated"

_USER_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_NOW = datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC)

_BENCH_ID = UUID("11111111-1111-1111-1111-111111111111")
_SQUAT_ID = UUID("22222222-2222-2222-2222-222222222222")
_RUN_ID = UUID("33333333-3333-3333-3333-333333333333")

_BENCH = ExerciseRecord(
    id=_BENCH_ID,
    name="Bench Press",
    category="strength",
    muscle_group="mid_chest",
    secondary_muscle_groups=["triceps", "shoulders"],
    equipment="barbell",
    instructions=None,
    demo_url=None,
    is_custom=False,
    created_by=None,
    created_at=datetime(2026, 5, 1, 10, 0, 0, tzinfo=UTC),
    updated_at=_NOW,
)

_SQUAT = ExerciseRecord(
    id=_SQUAT_ID,
    name="Back Squat",
    category="strength",
    muscle_group="quads",
    secondary_muscle_groups=["glutes", "hamstrings"],
    equipment="barbell",
    instructions=None,
    demo_url=None,
    is_custom=False,
    created_by=None,
    created_at=datetime(2026, 5, 2, 10, 0, 0, tzinfo=UTC),
    updated_at=_NOW,
)

_RUN = ExerciseRecord(
    id=_RUN_ID,
    name="Treadmill Run",
    category="cardio",
    muscle_group="full_body",
    secondary_muscle_groups=[],
    equipment="cardio_machine",
    instructions=None,
    demo_url=None,
    is_custom=False,
    created_by=None,
    created_at=datetime(2026, 5, 3, 10, 0, 0, tzinfo=UTC),
    updated_at=_NOW,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_token(user_id: UUID = _USER_ID, expired: bool = False) -> str:
    now = datetime.now(UTC)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    payload: dict[str, Any] = {
        "exp": exp,
        "aud": _AUDIENCE,
        "role": "authenticated",
        "sub": str(user_id),
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_make_token()}"}


# ── Fake repository ───────────────────────────────────────────────────────────


class FakeExerciseRepository:
    """
    In-memory ExerciseRepository for unit tests.

    Text search (q) uses case-insensitive substring matching as a proxy for
    trigram similarity. The real implementation uses PostgreSQL pg_trgm.

    Ordering mirrors the production implementation:
      - When q: similarity (substring proxy), then created_at DESC, id DESC
      - When q absent: created_at DESC, id DESC

    Cursor pagination uses (created_at DESC, id DESC) composite in both modes,
    matching Decision 94 and the exercises router.
    """

    def __init__(self, exercises: list[ExerciseRecord] | None = None) -> None:
        self._store: dict[UUID, ExerciseRecord] = {}
        for ex in exercises or []:
            self._store[ex.id] = ex

    async def list_exercises(
        self,
        q: str | None,
        muscle_group: str | None,
        equipment: str | None,
        category: str | None,
        limit: int,
        cursor_created_at: datetime | None,
        cursor_id: UUID | None,
    ) -> tuple[list[ExerciseRecord], bool]:
        records = list(self._store.values())

        # Apply attribute filters
        if muscle_group is not None:
            records = [r for r in records if r.muscle_group == muscle_group]
        if equipment is not None:
            records = [r for r in records if r.equipment == equipment]
        if category is not None:
            records = [r for r in records if r.category == category]

        # Apply text search (substring proxy for trigram similarity)
        if q is not None:
            term = q.lower()
            records = [r for r in records if term in r.name.lower()]

        # Sort: created_at DESC, id DESC (matches cursor keyset)
        records.sort(key=lambda r: (r.created_at, r.id), reverse=True)

        # Apply cursor filter
        if cursor_created_at is not None and cursor_id is not None:
            records = [
                r
                for r in records
                if (r.created_at, r.id) < (cursor_created_at, cursor_id)
            ]

        fetched = records[: limit + 1]
        has_more = len(fetched) > limit
        return fetched[:limit], has_more


# ── Fixture helpers ───────────────────────────────────────────────────────────


def _make_client(repo: FakeExerciseRepository) -> TestClient:
    from app.repositories.exercise_repository import get_exercise_repository
    from main import app

    app.dependency_overrides[get_exercise_repository] = lambda: repo
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Generator[None, None, None]:
    yield
    from main import app

    app.dependency_overrides.clear()


# ── GET /v1/exercises — text search ──────────────────────────────────────────


class TestExerciseTextSearch:
    def test_q_filters_by_name_substring(self) -> None:
        repo = FakeExerciseRepository([_BENCH, _SQUAT, _RUN])
        client = _make_client(repo)

        response = client.get("/v1/exercises?q=bench", headers=_auth())

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Bench Press"

    def test_q_is_case_insensitive(self) -> None:
        repo = FakeExerciseRepository([_BENCH, _SQUAT])
        client = _make_client(repo)

        response = client.get("/v1/exercises?q=BENCH", headers=_auth())

        assert response.status_code == 200
        assert len(response.json()["data"]) == 1

    def test_q_no_match_returns_200_empty(self) -> None:
        repo = FakeExerciseRepository([_BENCH, _SQUAT])
        client = _make_client(repo)

        response = client.get("/v1/exercises?q=deadlift", headers=_auth())

        assert response.status_code == 200
        body = response.json()
        assert body["data"] == []
        assert body["has_more"] is False
        assert body["next_cursor"] is None

    def test_q_partial_match_works(self) -> None:
        repo = FakeExerciseRepository([_BENCH, _SQUAT, _RUN])
        client = _make_client(repo)

        # "squat" matches "Back Squat"
        response = client.get("/v1/exercises?q=squat", headers=_auth())

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Back Squat"


# ── GET /v1/exercises — attribute filters ─────────────────────────────────────


class TestExerciseFilters:
    def test_muscle_group_filter(self) -> None:
        repo = FakeExerciseRepository([_BENCH, _SQUAT, _RUN])
        client = _make_client(repo)

        response = client.get("/v1/exercises?muscle_group=quads", headers=_auth())

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Back Squat"

    def test_equipment_filter(self) -> None:
        repo = FakeExerciseRepository([_BENCH, _SQUAT, _RUN])
        client = _make_client(repo)

        response = client.get("/v1/exercises?equipment=cardio_machine", headers=_auth())

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Treadmill Run"

    def test_category_filter(self) -> None:
        repo = FakeExerciseRepository([_BENCH, _SQUAT, _RUN])
        client = _make_client(repo)

        response = client.get("/v1/exercises?category=strength", headers=_auth())

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2

    def test_filter_no_match_returns_200_empty(self) -> None:
        repo = FakeExerciseRepository([_BENCH])
        client = _make_client(repo)

        response = client.get("/v1/exercises?muscle_group=biceps", headers=_auth())

        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_combined_search_and_filter(self) -> None:
        """q + muscle_group must both be satisfied — AND semantics."""
        dumbbell_press = ExerciseRecord(
            id=uuid4(),
            name="Dumbbell Press",
            category="strength",
            muscle_group="mid_chest",
            secondary_muscle_groups=[],
            equipment="dumbbell",
            instructions=None,
            demo_url=None,
            is_custom=False,
            created_by=None,
            created_at=datetime(2026, 5, 4, 10, 0, 0, tzinfo=UTC),
            updated_at=_NOW,
        )
        repo = FakeExerciseRepository([_BENCH, _SQUAT, dumbbell_press])
        client = _make_client(repo)

        # "press" matches Bench Press + Dumbbell Press; mid_chest narrows both
        response = client.get(
            "/v1/exercises?q=press&muscle_group=mid_chest", headers=_auth()
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2
        names = {d["name"] for d in data}
        assert names == {"Bench Press", "Dumbbell Press"}

    def test_combined_search_and_filter_no_match_returns_200_empty(self) -> None:
        repo = FakeExerciseRepository([_BENCH, _SQUAT])
        client = _make_client(repo)

        # "bench" matches Bench Press but muscle_group=quads does not
        response = client.get(
            "/v1/exercises?q=bench&muscle_group=quads", headers=_auth()
        )

        assert response.status_code == 200
        assert response.json()["data"] == []


# ── GET /v1/exercises — empty results ────────────────────────────────────────


class TestExerciseEmptyResults:
    def test_empty_library_returns_200_not_404(self) -> None:
        repo = FakeExerciseRepository()
        client = _make_client(repo)

        response = client.get("/v1/exercises", headers=_auth())

        assert response.status_code == 200
        body = response.json()
        assert body["data"] == []
        assert body["has_more"] is False
        assert body["next_cursor"] is None

    def test_response_envelope_fields_always_present(self) -> None:
        repo = FakeExerciseRepository()
        client = _make_client(repo)

        response = client.get("/v1/exercises", headers=_auth())

        body = response.json()
        assert {"data", "next_cursor", "has_more"}.issubset(body.keys())

    def test_returns_401_when_unauthenticated(self) -> None:
        repo = FakeExerciseRepository([_BENCH])
        client = _make_client(repo)

        response = client.get("/v1/exercises")

        assert response.status_code == 401
        assert response.json()["error_code"] == "auth_token_missing"


# ── GET /v1/exercises — cursor pagination ────────────────────────────────────


def _make_exercise_at(created_at: datetime, name: str = "Exercise") -> ExerciseRecord:
    return ExerciseRecord(
        id=uuid4(),
        name=name,
        category="strength",
        muscle_group="quads",
        secondary_muscle_groups=[],
        equipment="barbell",
        instructions=None,
        demo_url=None,
        is_custom=False,
        created_by=None,
        created_at=created_at,
        updated_at=_NOW,
    )


class TestExercisePagination:
    def test_first_page_returns_correct_items_and_cursor(self) -> None:
        exercises = [
            _make_exercise_at(
                datetime(2026, 5, i + 1, 10, 0, 0, tzinfo=UTC), f"E{i + 1}"
            )
            for i in range(5)
        ]
        repo = FakeExerciseRepository(exercises)
        client = _make_client(repo)

        response = client.get("/v1/exercises?limit=3", headers=_auth())

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 3
        assert body["has_more"] is True
        assert body["next_cursor"] is not None
        # created_at DESC — newest first
        assert body["data"][0]["name"] == "E5"

    def test_second_page_follows_first_without_gaps(self) -> None:
        exercises = [
            _make_exercise_at(
                datetime(2026, 5, i + 1, 10, 0, 0, tzinfo=UTC), f"E{i + 1}"
            )
            for i in range(5)
        ]
        repo = FakeExerciseRepository(exercises)
        client = _make_client(repo)

        first = client.get("/v1/exercises?limit=3", headers=_auth())
        cursor = first.json()["next_cursor"]

        second = client.get(f"/v1/exercises?limit=3&cursor={cursor}", headers=_auth())

        assert second.status_code == 200
        body = second.json()
        # Remaining 2 items after E5, E4, E3
        assert len(body["data"]) == 2
        assert body["has_more"] is False
        assert body["next_cursor"] is None
        assert body["data"][0]["name"] == "E2"
        assert body["data"][1]["name"] == "E1"

    def test_last_page_has_more_false_no_cursor(self) -> None:
        repo = FakeExerciseRepository([_BENCH])
        client = _make_client(repo)

        response = client.get("/v1/exercises?limit=20", headers=_auth())

        assert response.status_code == 200
        assert response.json()["has_more"] is False
        assert response.json()["next_cursor"] is None

    def test_invalid_cursor_returns_400(self) -> None:
        repo = FakeExerciseRepository()
        client = _make_client(repo)

        response = client.get("/v1/exercises?cursor=!!!invalid!!!", headers=_auth())

        assert response.status_code == 400
        assert response.json()["error_code"] == "exercise_cursor_invalid"

    def test_limit_zero_returns_400(self) -> None:
        repo = FakeExerciseRepository()
        client = _make_client(repo)

        assert client.get("/v1/exercises?limit=0", headers=_auth()).status_code == 400

    def test_limit_over_100_returns_400(self) -> None:
        repo = FakeExerciseRepository()
        client = _make_client(repo)

        assert client.get("/v1/exercises?limit=101", headers=_auth()).status_code == 400

    def test_limit_1_accepted(self) -> None:
        repo = FakeExerciseRepository([_BENCH])
        client = _make_client(repo)

        assert client.get("/v1/exercises?limit=1", headers=_auth()).status_code == 200

    def test_limit_100_accepted(self) -> None:
        repo = FakeExerciseRepository([_BENCH])
        client = _make_client(repo)

        assert client.get("/v1/exercises?limit=100", headers=_auth()).status_code == 200

    def test_pagination_with_filter_preserves_filter(self) -> None:
        """Cursor pages through filtered results without leaking unfiltered rows."""
        strength = [
            _make_exercise_at(
                datetime(2026, 5, i + 1, 10, 0, 0, tzinfo=UTC), f"Strength{i + 1}"
            )
            for i in range(4)
        ]
        cardio = ExerciseRecord(
            id=uuid4(),
            name="Cardio Exercise",
            category="cardio",
            muscle_group="full_body",
            secondary_muscle_groups=[],
            equipment="cardio_machine",
            instructions=None,
            demo_url=None,
            is_custom=False,
            created_by=None,
            created_at=datetime(2026, 5, 10, 10, 0, 0, tzinfo=UTC),
            updated_at=_NOW,
        )
        repo = FakeExerciseRepository(strength + [cardio])
        client = _make_client(repo)

        first = client.get("/v1/exercises?category=strength&limit=2", headers=_auth())
        assert first.status_code == 200
        assert len(first.json()["data"]) == 2
        cursor = first.json()["next_cursor"]

        second = client.get(
            f"/v1/exercises?category=strength&limit=2&cursor={cursor}",
            headers=_auth(),
        )
        assert second.status_code == 200
        data = second.json()["data"]
        # Only strength exercises on page 2 — cardio must not appear
        assert all(d["category"] == "strength" for d in data)


# ── GIN index assertion (real-DB integration test) ────────────────────────────

_REAL_DB_AVAILABLE = os.environ.get("ENVIRONMENT") != "test"


@pytest.mark.skipif(
    not _REAL_DB_AVAILABLE,
    reason=(
        "Integration test — requires a real PostgreSQL instance with pg_trgm "
        "and the idx_exercise_name_trgm GIN index. "
        "Run locally with ENVIRONMENT=development and a valid DATABASE_URL."
    ),
)
def test_exercise_text_search_uses_gin_index_not_seq_scan() -> None:
    """
    Verifies that a trigram similarity query on the exercise name column uses
    the GIN index (idx_exercise_name_trgm) rather than a sequential scan.

    A sequential scan on a large exercise table would exceed the 200ms
    performance target (docs/ARCHITECTURE.md Decision 94).

    Uses EXPLAIN (ANALYZE, FORMAT JSON) so the assertion is against the actual
    plan chosen by the PostgreSQL query planner, not a hypothetical plan.
    """
    import json
    import os as _os

    from sqlalchemy import create_engine, text

    db_url = _os.environ["DATABASE_URL"]
    engine = create_engine(db_url)

    explain_sql = text(
        "EXPLAIN (ANALYZE, FORMAT JSON) "
        "SELECT id, name, similarity(name, :q) AS sim "
        "FROM exercise "
        "WHERE similarity(name, :q) > 0.1 "
        "ORDER BY sim DESC, created_at DESC, id DESC "
        "LIMIT 20"
    )

    with engine.connect() as conn:
        result = conn.execute(explain_sql, {"q": "bench press"})
        raw = result.scalar()
        assert isinstance(raw, str)
        plan_json = json.loads(raw)

    plan_text = json.dumps(plan_json)

    # The GIN index must appear in the plan — a bitmap index scan or index scan
    # on idx_exercise_name_trgm confirms the planner chose the index.
    assert "idx_exercise_name_trgm" in plan_text, (
        "Query plan does not reference idx_exercise_name_trgm. "
        "Ensure the GIN index exists: "
        "CREATE INDEX idx_exercise_name_trgm ON exercise USING gin(name gin_trgm_ops)"
    )

    # Confirm no top-level sequential scan on the exercises table.
    assert (
        plan_text.count('"Seq Scan"') == 0
        or "exercise" not in plan_text.split('"Seq Scan"')[1][:200]
    ), (
        "Query plan shows a sequential scan on exercise — GIN index not used. "
        "Check pg_trgm is enabled and index stats are up to date (ANALYZE)."
    )


# ── Repository internals ──────────────────────────────────────────────────────


async def test_get_exercise_repository_raises_runtime_error() -> None:
    """The default get_exercise_repository must always be overridden in production."""
    from app.repositories.exercise_repository import get_exercise_repository

    with pytest.raises(RuntimeError, match="get_exercise_repository"):
        await get_exercise_repository()
