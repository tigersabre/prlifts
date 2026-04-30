"""
schemas.py
PRLifts Backend

Shared Pydantic response schemas used across all API endpoints.
Putting them here keeps routers thin and avoids circular imports —
auth, routers, and middleware can all reference these without depending
on each other.

See docs/ERROR_CATALOG.md for all valid error codes and user-facing messages.
See docs/STANDARDS.md § 7.5 API Error Response Standard.
"""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class ErrorResponse(BaseModel):
    """
    Standard error response body for all backend error responses.

    error_code is machine-readable and drives client-side behaviour (e.g. sign-out).
    message is safe to display directly to users — never contains internal detail.
    request_id is the correlation_id so users can quote it to support.

    See docs/ERROR_CATALOG.md for every valid error_code and its matching message.
    """

    error_code: str
    message: str
    request_id: str


# ── User enums ────────────────────────────────────────────────────────────────


class WeightUnit(StrEnum):
    kg = "kg"
    lbs = "lbs"


class MeasurementUnit(StrEnum):
    cm = "cm"
    inches = "inches"


class Gender(StrEnum):
    male = "male"
    female = "female"
    na = "na"


class UserGoal(StrEnum):
    build_muscle = "build_muscle"
    lose_fat = "lose_fat"
    improve_endurance = "improve_endurance"
    athletic_performance = "athletic_performance"
    general_fitness = "general_fitness"


class BetaTier(StrEnum):
    none = "none"
    tester = "tester"
    full_access = "full_access"


# ── User request / response models ───────────────────────────────────────────

_DISPLAY_NAME_MAX_LEN = 50


def _validate_display_name(value: str | None) -> str | None:
    """Strip whitespace only. Length is enforced by routers for correct error codes."""
    if value is None:
        return None
    return value.strip()


class UserResponse(BaseModel):
    """
    User profile returned by GET /v1/users/me, POST /v1/users, and
    PATCH /v1/users/me. Mirrors the user table schema exactly.

    See docs/SCHEMA.md — user table.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str | None
    display_name: str | None
    avatar_url: str | None
    unit_preference: WeightUnit
    measurement_unit: MeasurementUnit
    date_of_birth: date | None
    gender: Gender
    goal: UserGoal | None
    beta_tier: BetaTier
    created_at: datetime
    updated_at: datetime


class CreateUserRequest(BaseModel):
    """
    Request body for POST /v1/users. Creates the app-level user profile
    after Supabase Auth has already created the auth record.

    user_id is taken from the JWT sub — never from the request body.
    display_name is trimmed and must be ≤ 50 characters after trimming.
    """

    display_name: str | None = None
    unit_preference: WeightUnit = WeightUnit.lbs
    measurement_unit: MeasurementUnit = MeasurementUnit.cm

    @field_validator("display_name")
    @classmethod
    def trim_and_validate_display_name(cls, v: str | None) -> str | None:
        return _validate_display_name(v)


class UpdateUserRequest(BaseModel):
    """
    Request body for PATCH /v1/users/me. All fields are optional.
    Only fields present in the request body are updated (model_fields_set).

    Nullable fields (display_name, date_of_birth, goal) may be explicitly
    set to null to clear them. Non-nullable fields (unit_preference,
    measurement_unit, gender) are ignored if null.
    """

    display_name: str | None = None
    unit_preference: WeightUnit | None = None
    measurement_unit: MeasurementUnit | None = None
    date_of_birth: date | None = None
    gender: Gender | None = None
    goal: UserGoal | None = None

    @field_validator("display_name")
    @classmethod
    def trim_and_validate_display_name(cls, v: str | None) -> str | None:
        return _validate_display_name(v)
