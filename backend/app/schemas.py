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

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


# ── Workout enums ─────────────────────────────────────────────────────────────


class WorkoutStatus(StrEnum):
    in_progress = "in_progress"
    paused = "paused"
    partial_completion = "partial_completion"
    completed = "completed"


class WorkoutType(StrEnum):
    ad_hoc = "ad_hoc"
    planned = "planned"


class WorkoutFormat(StrEnum):
    weightlifting = "weightlifting"
    cardio = "cardio"
    mixed = "mixed"
    other = "other"


class WorkoutLocation(StrEnum):
    gym = "gym"
    home = "home"
    outdoor = "outdoor"
    other = "other"


# ── Workout request / response models ─────────────────────────────────────────


class WorkoutResponse(BaseModel):
    """
    Workout returned by POST /v1/workouts, GET /v1/workouts/{id}, and
    PATCH /v1/workouts/{id}. Mirrors the workout table schema.

    server_received_at is omitted — it is backend-only and never exposed
    to clients. See docs/SCHEMA.md — workout table.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str | None
    notes: str | None
    status: WorkoutStatus
    type: WorkoutType
    format: WorkoutFormat
    plan_id: UUID | None
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: int | None
    location: WorkoutLocation | None
    rating: int | None
    created_at: datetime
    updated_at: datetime


class WorkoutListResponse(BaseModel):
    """Paginated response for GET /v1/workouts."""

    data: list[WorkoutResponse]
    total: int
    page: int
    per_page: int
    has_more: bool


class CreateWorkoutRequest(BaseModel):
    """
    Request body for POST /v1/workouts. type and format are required.

    client_started_at allows the iOS client to provide the user-perceived
    start time. server_received_at is always assigned server-side and governs
    conflict resolution — it is never read from this payload.
    """

    type: WorkoutType
    format: WorkoutFormat
    name: str | None = Field(default=None, max_length=200)
    location: WorkoutLocation | None = None
    plan_id: UUID | None = None
    client_started_at: datetime | None = None


class UpdateWorkoutRequest(BaseModel):
    """
    Request body for PATCH /v1/workouts/{id}. All fields are optional.
    Only fields present in the request body are updated (model_fields_set).

    When status is set to completed the server assigns completed_at —
    any client-provided completed_at is ignored for that transition.
    """

    name: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=5000)
    status: WorkoutStatus | None = None
    rating: int | None = Field(default=None, ge=1, le=5)


# ── WorkoutExercise / WorkoutSet enums ────────────────────────────────────────


class SetType(StrEnum):
    normal = "normal"
    warmup = "warmup"
    dropset = "dropset"
    failure = "failure"
    pr = "pr"


class WeightModifier(StrEnum):
    none = "none"
    assisted = "assisted"
    weighted = "weighted"


# ── WorkoutExercise schemas ───────────────────────────────────────────────────


class WorkoutExerciseResponse(BaseModel):
    """
    WorkoutExercise returned by POST /v1/workout-exercises.
    Mirrors workout_exercise table. See docs/SCHEMA.md — workout_exercise table.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workout_id: UUID
    exercise_id: UUID
    order_index: int
    notes: str | None
    rest_seconds: int | None
    created_at: datetime
    updated_at: datetime


class CreateWorkoutExerciseRequest(BaseModel):
    """
    Request body for POST /v1/workout-exercises.
    workout_id ownership is verified against the JWT sub before creation.
    """

    workout_id: UUID
    exercise_id: UUID
    order_index: int = Field(ge=0)
    notes: str | None = Field(default=None, max_length=2000)
    rest_seconds: int | None = Field(default=None, ge=0, le=3600)


# ── WorkoutSet schemas ────────────────────────────────────────────────────────


class WorkoutSetResponse(BaseModel):
    """
    WorkoutSet returned by POST, PATCH /v1/workout-sets.
    is_personal_record is computed after PR detection — not stored.
    See docs/SCHEMA.md — workout_set table.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workout_exercise_id: UUID
    set_number: int
    set_type: SetType
    weight: float | None = None
    weight_unit: WeightUnit | None = None
    weight_modifier: WeightModifier
    modifier_value: float | None = None
    modifier_unit: WeightUnit | None = None
    reps: int | None = None
    duration_seconds: int | None = None
    distance_meters: float | None = None
    calories: int | None = None
    rpe: int | None = None
    is_completed: bool
    notes: str | None = None
    is_personal_record: bool = False
    created_at: datetime
    updated_at: datetime


class CreateWorkoutSetRequest(BaseModel):
    """
    Request body for POST /v1/workout-sets.
    At least one of weight, reps, duration_seconds, or distance_meters must be set
    (mirrors the must_have_metric DB constraint).
    client_created_at is context only — server_received_at governs conflict resolution.
    """

    workout_exercise_id: UUID
    set_number: int = Field(ge=1, le=100)
    set_type: SetType = SetType.normal
    weight: float | None = Field(default=None, ge=0, le=2000)
    weight_unit: WeightUnit | None = None
    weight_modifier: WeightModifier = WeightModifier.none
    modifier_value: float | None = Field(default=None, ge=0, le=500)
    modifier_unit: WeightUnit | None = None
    reps: int | None = Field(default=None, ge=0, le=1000)
    duration_seconds: int | None = Field(default=None, ge=0, le=86400)
    distance_meters: float | None = Field(default=None, ge=0, le=100000)
    calories: int | None = Field(default=None, ge=0, le=10000)
    rpe: int | None = Field(default=None, ge=1, le=10)
    is_completed: bool = False
    notes: str | None = Field(default=None, max_length=2000)
    client_created_at: datetime | None = None

    @model_validator(mode="after")
    def must_have_metric(self) -> "CreateWorkoutSetRequest":
        if all(
            v is None
            for v in [
                self.weight,
                self.reps,
                self.duration_seconds,
                self.distance_meters,
            ]
        ):
            raise ValueError(
                "At least one of weight, reps, duration_seconds, "
                "or distance_meters must be set."
            )
        return self


class UpdateWorkoutSetRequest(BaseModel):
    """
    Request body for PATCH /v1/workout-sets/{id}. All fields are optional.
    Only fields present in the request body are updated (model_fields_set).
    """

    weight: float | None = Field(default=None, ge=0, le=2000)
    weight_unit: WeightUnit | None = None
    weight_modifier: WeightModifier | None = None
    modifier_value: float | None = Field(default=None, ge=0, le=500)
    modifier_unit: WeightUnit | None = None
    reps: int | None = Field(default=None, ge=0, le=1000)
    duration_seconds: int | None = Field(default=None, ge=0, le=86400)
    distance_meters: float | None = Field(default=None, ge=0, le=100000)
    calories: int | None = Field(default=None, ge=0, le=10000)
    rpe: int | None = Field(default=None, ge=1, le=10)
    is_completed: bool | None = None
    notes: str | None = Field(default=None, max_length=2000)
