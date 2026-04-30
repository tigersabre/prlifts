"""
test_users.py
PRLifts Backend Tests

Unit tests for the user profile endpoints:
  POST   /v1/users       — create profile
  GET    /v1/users/me    — read own profile
  PATCH  /v1/users/me    — partial update

Each test class isolates its own FakeUserRepository via dependency_overrides
so tests never share mutable state.

See docs/ERROR_CATALOG.md — auth_ and user_ error codes.
See GitHub Issue #35 for acceptance criteria.
"""

import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient

from app.repositories.user_repository import UserRecord

# ── Constants ────────────────────────────────────────────────────────────────

_SECRET: str = os.environ.get(
    "SUPABASE_JWT_SECRET", "test-supabase-jwt-secret-for-unit-tests"
)
_ALGORITHM = "HS256"
_AUDIENCE = "authenticated"
_USER_A_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_USER_B_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

_DEFAULT_RECORD = UserRecord(
    id=_USER_A_ID,
    email="a@example.com",
    display_name="Alice",
    avatar_url=None,
    unit_preference="lbs",
    measurement_unit="cm",
    date_of_birth=None,
    gender="na",
    goal=None,
    beta_tier="none",
    created_at=datetime(2026, 4, 1, tzinfo=UTC),
    updated_at=datetime(2026, 4, 1, tzinfo=UTC),
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_token(user_id: UUID = _USER_A_ID, expired: bool = False) -> str:
    now = datetime.now(UTC)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    payload: dict[str, Any] = {
        "exp": exp,
        "aud": _AUDIENCE,
        "role": "authenticated",
        "sub": str(user_id),
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def _auth(user_id: UUID = _USER_A_ID) -> dict[str, str]:
    return {"Authorization": f"Bearer {_make_token(user_id)}"}


# ── Fake repository ───────────────────────────────────────────────────────────


class FakeUserRepository:
    """
    In-memory UserRepository for unit tests.

    Stores records keyed by user_id. Each test class creates a fresh instance
    via dependency_overrides so state never leaks between tests.
    """

    def __init__(self, initial: UserRecord | None = None) -> None:
        self._store: dict[UUID, UserRecord] = {}
        if initial is not None:
            self._store[initial.id] = initial

    async def exists(self, user_id: UUID) -> bool:
        return user_id in self._store

    async def create(
        self,
        user_id: UUID,
        display_name: str | None,
        unit_preference: str,
        measurement_unit: str,
    ) -> UserRecord:
        now = datetime.now(UTC)
        record = UserRecord(
            id=user_id,
            email=None,
            display_name=display_name,
            avatar_url=None,
            unit_preference=unit_preference,
            measurement_unit=measurement_unit,
            date_of_birth=None,
            gender="na",
            goal=None,
            beta_tier="none",
            created_at=now,
            updated_at=now,
        )
        self._store[user_id] = record
        return record

    async def get_by_id(self, user_id: UUID) -> UserRecord | None:
        return self._store.get(user_id)

    async def update(
        self,
        user_id: UUID,
        updates: dict[str, object],
    ) -> UserRecord | None:
        record = self._store.get(user_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        updated = UserRecord(
            id=record.id,
            email=record.email,
            display_name=updates.get("display_name", record.display_name),  # type: ignore[arg-type]
            avatar_url=record.avatar_url,
            unit_preference=str(updates.get("unit_preference", record.unit_preference)),
            measurement_unit=str(
                updates.get("measurement_unit", record.measurement_unit)
            ),
            date_of_birth=updates.get("date_of_birth", record.date_of_birth),  # type: ignore[arg-type]
            gender=str(updates.get("gender", record.gender)),
            goal=updates.get("goal", record.goal),  # type: ignore[arg-type]
            beta_tier=record.beta_tier,
            created_at=record.created_at,
            updated_at=now,
        )
        self._store[user_id] = updated
        return updated


# ── Fixture helpers ───────────────────────────────────────────────────────────


def _make_client(repo: FakeUserRepository) -> TestClient:
    """Returns a TestClient with the given repo wired as the dependency."""
    from app.repositories.user_repository import get_user_repository
    from main import app

    app.dependency_overrides[get_user_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    return client


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Generator[None, None, None]:
    yield
    from main import app

    app.dependency_overrides.clear()


# ── POST /v1/users ────────────────────────────────────────────────────────────


class TestCreateUser:
    def test_creates_profile_and_returns_201(self) -> None:
        repo = FakeUserRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/users",
            json={
                "display_name": "Alice",
                "unit_preference": "kg",
                "measurement_unit": "cm",
            },
            headers=_auth(),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(_USER_A_ID)
        assert data["display_name"] == "Alice"
        assert data["unit_preference"] == "kg"
        assert data["measurement_unit"] == "cm"
        assert data["beta_tier"] == "none"
        assert "created_at" in data
        assert "updated_at" in data

    def test_user_id_matches_jwt_sub(self) -> None:
        repo = FakeUserRepository()
        client = _make_client(repo)

        response = client.post("/v1/users", json={}, headers=_auth(_USER_A_ID))

        assert response.status_code == 201
        assert response.json()["id"] == str(_USER_A_ID)

    def test_display_name_is_trimmed(self) -> None:
        repo = FakeUserRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/users",
            json={"display_name": "  Bob  "},
            headers=_auth(),
        )

        assert response.status_code == 201
        assert response.json()["display_name"] == "Bob"

    def test_defaults_applied_when_optional_fields_omitted(self) -> None:
        repo = FakeUserRepository()
        client = _make_client(repo)

        response = client.post("/v1/users", json={}, headers=_auth())

        assert response.status_code == 201
        data = response.json()
        assert data["unit_preference"] == "lbs"
        assert data["measurement_unit"] == "cm"
        assert data["display_name"] is None

    def test_returns_409_when_profile_already_exists(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.post(
            "/v1/users",
            json={"display_name": "Alice"},
            headers=_auth(),
        )

        assert response.status_code == 409
        assert response.json()["error_code"] == "user_profile_exists"

    def test_returns_401_when_unauthenticated(self) -> None:
        repo = FakeUserRepository()
        client = _make_client(repo)

        response = client.post("/v1/users", json={"display_name": "Alice"})

        assert response.status_code == 401
        assert response.json()["error_code"] == "auth_token_missing"

    def test_returns_422_when_display_name_exceeds_50_chars(self) -> None:
        repo = FakeUserRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/users",
            json={"display_name": "A" * 51},
            headers=_auth(),
        )

        assert response.status_code == 422
        assert response.json()["error_code"] == "user_display_name_too_long"

    def test_returns_422_when_display_name_exceeds_50_chars_after_trim(self) -> None:
        repo = FakeUserRepository()
        client = _make_client(repo)

        # 51 chars after trimming is also invalid
        response = client.post(
            "/v1/users",
            json={"display_name": "  " + "A" * 51},
            headers=_auth(),
        )

        assert response.status_code == 422
        assert response.json()["error_code"] == "user_display_name_too_long"

    def test_accepts_display_name_exactly_50_chars(self) -> None:
        repo = FakeUserRepository()
        client = _make_client(repo)

        response = client.post(
            "/v1/users",
            json={"display_name": "A" * 50},
            headers=_auth(),
        )

        assert response.status_code == 201
        assert len(response.json()["display_name"]) == 50

    def test_request_id_present_in_error_response(self) -> None:
        repo = FakeUserRepository()
        client = _make_client(repo)

        response = client.post("/v1/users", json={})

        assert response.status_code == 401
        assert "request_id" in response.json()


# ── GET /v1/users/me ──────────────────────────────────────────────────────────


class TestGetMe:
    def test_returns_own_profile(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.get("/v1/users/me", headers=_auth())

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(_USER_A_ID)
        assert data["display_name"] == "Alice"

    def test_returns_401_when_unauthenticated(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.get("/v1/users/me")

        assert response.status_code == 401
        assert response.json()["error_code"] == "auth_token_missing"

    def test_returns_404_when_profile_does_not_exist(self) -> None:
        repo = FakeUserRepository()  # empty store
        client = _make_client(repo)

        response = client.get("/v1/users/me", headers=_auth())

        assert response.status_code == 404
        assert response.json()["error_code"] == "user_not_found"

    def test_returns_401_for_expired_token(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        expired_token = _make_token(expired=True)
        response = client.get(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401
        assert response.json()["error_code"] == "auth_token_expired"

    def test_error_response_has_request_id(self) -> None:
        repo = FakeUserRepository()
        client = _make_client(repo)

        response = client.get("/v1/users/me", headers=_auth())

        assert response.status_code == 404
        assert "request_id" in response.json()

    def test_idor_protection_other_user_path_returns_404(self) -> None:
        # GET /v1/users/{any-uuid} does not exist — 404 proves no IDOR vector.
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.get(f"/v1/users/{_USER_B_ID}", headers=_auth())

        assert response.status_code == 404

    def test_user_a_cannot_see_user_b_data(self) -> None:
        # User B's record exists; User A's JWT cannot access it via /me.
        b_record = UserRecord(
            id=_USER_B_ID,
            email="b@example.com",
            display_name="Bob",
            avatar_url=None,
            unit_preference="kg",
            measurement_unit="cm",
            date_of_birth=None,
            gender="male",
            goal=None,
            beta_tier="none",
            created_at=datetime(2026, 4, 1, tzinfo=UTC),
            updated_at=datetime(2026, 4, 1, tzinfo=UTC),
        )
        repo = FakeUserRepository(initial=b_record)
        client = _make_client(repo)

        # User A is authenticated but has no profile in the store.
        response = client.get("/v1/users/me", headers=_auth(_USER_A_ID))

        # User A's /me lookup uses their own user_id — they get 404, not Bob's data.
        assert response.status_code == 404

    def test_response_includes_all_required_fields(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.get("/v1/users/me", headers=_auth())

        data = response.json()
        required = {
            "id",
            "unit_preference",
            "measurement_unit",
            "gender",
            "beta_tier",
            "created_at",
            "updated_at",
        }
        assert required.issubset(data.keys())


# ── PATCH /v1/users/me ────────────────────────────────────────────────────────


class TestUpdateMe:
    def test_updates_provided_fields_only(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            "/v1/users/me",
            json={"display_name": "Alicia"},
            headers=_auth(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Alicia"
        # unit_preference was not in the request body — must be unchanged
        assert data["unit_preference"] == "lbs"

    def test_updates_unit_preference(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            "/v1/users/me",
            json={"unit_preference": "kg"},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert response.json()["unit_preference"] == "kg"

    def test_clears_nullable_display_name(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            "/v1/users/me",
            json={"display_name": None},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert response.json()["display_name"] is None

    def test_sets_goal(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            "/v1/users/me",
            json={"goal": "build_muscle"},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert response.json()["goal"] == "build_muscle"

    def test_display_name_trimmed_on_update(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            "/v1/users/me",
            json={"display_name": "  Charlie  "},
            headers=_auth(),
        )

        assert response.status_code == 200
        assert response.json()["display_name"] == "Charlie"

    def test_empty_body_returns_current_profile_unchanged(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch("/v1/users/me", json={}, headers=_auth())

        assert response.status_code == 200
        assert response.json()["display_name"] == "Alice"

    def test_returns_401_when_unauthenticated(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch("/v1/users/me", json={"display_name": "X"})

        assert response.status_code == 401
        assert response.json()["error_code"] == "auth_token_missing"

    def test_returns_404_when_profile_does_not_exist(self) -> None:
        repo = FakeUserRepository()  # empty
        client = _make_client(repo)

        response = client.patch(
            "/v1/users/me",
            json={"display_name": "Ghost"},
            headers=_auth(),
        )

        assert response.status_code == 404
        assert response.json()["error_code"] == "user_not_found"

    def test_returns_422_when_display_name_exceeds_50_chars(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            "/v1/users/me",
            json={"display_name": "X" * 51},
            headers=_auth(),
        )

        assert response.status_code == 422
        assert response.json()["error_code"] == "user_display_name_too_long"

    def test_returns_422_with_correct_error_code_after_trim(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        # 51-char name with surrounding whitespace — still too long after trimming
        response = client.patch(
            "/v1/users/me",
            json={"display_name": "  " + "X" * 51},
            headers=_auth(),
        )

        assert response.status_code == 422
        assert response.json()["error_code"] == "user_display_name_too_long"

    def test_non_nullable_unit_preference_null_is_ignored(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        # Sending unit_preference: null — non-nullable, must be ignored
        response = client.patch(
            "/v1/users/me",
            json={"unit_preference": None, "display_name": "Alice2"},
            headers=_auth(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["unit_preference"] == "lbs"  # unchanged
        assert data["display_name"] == "Alice2"

    def test_updates_multiple_fields_at_once(self) -> None:
        repo = FakeUserRepository(initial=_DEFAULT_RECORD)
        client = _make_client(repo)

        response = client.patch(
            "/v1/users/me",
            json={
                "display_name": "Alicia",
                "unit_preference": "kg",
                "measurement_unit": "inches",
                "gender": "female",
            },
            headers=_auth(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Alicia"
        assert data["unit_preference"] == "kg"
        assert data["measurement_unit"] == "inches"
        assert data["gender"] == "female"

    def test_idor_patch_me_uses_jwt_user_id_not_path(self) -> None:
        # User B's record in the store; User A cannot overwrite it via /me.
        b_record = UserRecord(
            id=_USER_B_ID,
            email=None,
            display_name="Bob",
            avatar_url=None,
            unit_preference="kg",
            measurement_unit="cm",
            date_of_birth=None,
            gender="male",
            goal=None,
            beta_tier="none",
            created_at=datetime(2026, 4, 1, tzinfo=UTC),
            updated_at=datetime(2026, 4, 1, tzinfo=UTC),
        )
        repo = FakeUserRepository(initial=b_record)
        client = _make_client(repo)

        # Authenticating as User A, patching /me — User A has no profile.
        response = client.patch(
            "/v1/users/me",
            json={"display_name": "Hacker"},
            headers=_auth(_USER_A_ID),
        )

        # User A gets 404; Bob's record is untouched.
        assert response.status_code == 404
        assert repo._store[_USER_B_ID].display_name == "Bob"


# ── Repository and handler internals ─────────────────────────────────────────


async def test_get_user_repository_raises_runtime_error() -> None:
    """The default get_user_repository must always be overridden in production."""
    from app.repositories.user_repository import get_user_repository

    with pytest.raises(RuntimeError, match="get_user_repository"):
        await get_user_repository()


async def test_http_exception_handler_wraps_non_dict_detail() -> None:
    """Non-dict HTTPException details (e.g. Starlette 404 'Not Found') are
    returned under a 'detail' key, matching FastAPI's default behaviour."""
    from fastapi.exceptions import HTTPException

    from main import _http_exception_handler

    mock_request = object()
    exc = HTTPException(status_code=404, detail="Not Found")
    response = await _http_exception_handler(mock_request, exc)  # type: ignore[arg-type]

    assert response.status_code == 404
    import json

    body = json.loads(response.body)
    assert body == {"detail": "Not Found"}
