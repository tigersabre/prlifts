# PRLifts — Code Examples Reference

**Version:** 1.0
**Last updated:** April 2026
**Owner:** Staff/Principal Engineer
**Audience:** All developers (human and Claude Code)

> These are the canonical reference implementations for every
> major pattern in the codebase. When implementing a new feature,
> find the closest matching example here and follow it.
> Do not invent new patterns without updating this document.

---

## Backend Patterns

### Complete Route Handler

A thin route handler delegates immediately to a service.
No business logic in route functions.

```python
# routes/workout_sets.py

from uuid import UUID
from fastapi import APIRouter, Depends, status
from app.auth import get_current_user
from app.dependencies import get_workout_service
from app.models import User
from app.schemas import CreateWorkoutSetRequest, WorkoutSetResponse
from app.services.workout_service import WorkoutService

router = APIRouter(prefix="/v1/workout-sets", tags=["workout-sets"])


@router.post(
    "/",
    response_model=WorkoutSetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a completed workout set",
    description="""
    Records a single completed set within a workout exercise.
    Triggers PR detection when is_completed is true.
    Returns the saved set with is_personal_record populated.
    """,
)
async def log_workout_set(
    request: CreateWorkoutSetRequest,
    current_user: User = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
) -> WorkoutSetResponse:
    # Route function body should be 1–5 lines maximum.
    # Validate input (done by Pydantic), delegate to service, return response.
    workout_set = await workout_service.log_set(request, user_id=current_user.id)
    return WorkoutSetResponse.model_validate(workout_set)
```

---

### Complete Service Class

Services own all business logic. Dependencies are injected.

```python
# services/workout_service.py
# PRLifts Backend
#
# Handles all business logic for workout operations.
# The only place that coordinates between the database,
# PR detection, and AI job creation.

from uuid import UUID
from app.errors import WorkoutExerciseNotFoundError, UnauthorizedError
from app.models import WorkoutSet
from app.repositories.workout_repository import WorkoutRepository
from app.services.pr_detection_service import PRDetectionService
from app.schemas import CreateWorkoutSetRequest


class WorkoutService:
    """
    Handles all business logic for workout operations.

    This service is the only place that coordinates between
    the database, PR detection, and sync queue. Route handlers
    call this service — they do not touch the database directly.
    """

    def __init__(
        self,
        workout_repo: WorkoutRepository,
        pr_detector: PRDetectionService,
    ):
        # Dependencies injected — never instantiated inside the service
        self.workout_repo = workout_repo
        self.pr_detector = pr_detector

    async def log_set(
        self,
        set_data: CreateWorkoutSetRequest,
        user_id: UUID,
    ) -> WorkoutSet:
        """
        Saves a completed workout set and triggers PR detection.

        Args:
            set_data: Validated set data from the route handler
            user_id: The authenticated user's ID from the JWT

        Returns:
            The saved WorkoutSet with is_personal_record populated

        Raises:
            WorkoutExerciseNotFoundError: Workout exercise does not exist
            UnauthorizedError: Workout exercise does not belong to this user
        """
        # Verify ownership before any writes — never trust the client's claim
        workout_exercise = await self.workout_repo.get_exercise(
            set_data.workout_exercise_id
        )
        if workout_exercise is None:
            raise WorkoutExerciseNotFoundError(set_data.workout_exercise_id)
        if workout_exercise.workout.user_id != user_id:
            raise UnauthorizedError("workout_exercise", set_data.workout_exercise_id)

        # Save the set
        workout_set = await self.workout_repo.create_set(set_data, user_id)

        # Trigger PR detection on completed sets only
        if workout_set.is_completed:
            pr = await self.pr_detector.detect(workout_set, user_id)
            if pr:
                workout_set.is_personal_record = True

        return workout_set
```

---

### Error Handling Pattern

```python
# errors.py — domain exception hierarchy

class PRLiftsError(Exception):
    """Base exception for all PRLifts domain errors."""
    error_code: str = "system_error"
    status_code: int = 500
    user_message: str = "Something went wrong. We've been notified."


class WorkoutExerciseNotFoundError(PRLiftsError):
    """Raised when a workout exercise cannot be found."""
    error_code = "workout_exercise_not_found"
    status_code = 404
    user_message = "This exercise entry could not be found."

    def __init__(self, exercise_id: UUID):
        self.exercise_id = exercise_id
        super().__init__(f"WorkoutExercise {exercise_id} not found")


class UnauthorizedError(PRLiftsError):
    """Raised when a user attempts to access a resource they do not own."""
    error_code = "workout_not_owned"
    status_code = 403
    user_message = "You don't have access to this workout."

    def __init__(self, resource_type: str, resource_id: UUID):
        super().__init__(f"{resource_type} {resource_id} not owned by requesting user")
```

```python
# Exception handler registered in FastAPI app startup
@app.exception_handler(PRLiftsError)
async def prlifts_error_handler(request: Request, exc: PRLiftsError):
    logger.warning(
        "Domain error",
        error_code=exc.error_code,
        correlation_id=request.state.correlation_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.user_message,
            "request_id": str(request.state.correlation_id),
        },
    )
```

---

### Pydantic Request Model

```python
# schemas/workout_sets.py

from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from app.enums import SetType, WeightModifier, WeightUnit


class CreateWorkoutSetRequest(BaseModel):
    """Request body for POST /v1/workout-sets."""

    model_config = ConfigDict(extra="forbid")  # reject unknown fields

    workout_exercise_id: UUID
    set_number: int = Field(ge=1, le=100)
    set_type: SetType = SetType.normal
    weight: Optional[float] = Field(None, ge=0, le=2000)
    weight_unit: Optional[WeightUnit] = None
    weight_modifier: WeightModifier = WeightModifier.none
    modifier_value: Optional[float] = Field(None, ge=0, le=500)
    modifier_unit: Optional[WeightUnit] = None
    reps: Optional[int] = Field(None, ge=0, le=1000)
    duration_seconds: Optional[int] = Field(None, ge=0, le=86400)
    distance_meters: Optional[float] = Field(None, ge=0, le=100000)
    calories: Optional[int] = Field(None, ge=0, le=10000)
    rpe: Optional[int] = Field(None, ge=1, le=10)
    is_completed: bool = False
    notes: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode="after")
    def must_have_at_least_one_metric(self) -> "CreateWorkoutSetRequest":
        """
        A set must record at least one measurement.
        This mirrors the database constraint for defence-in-depth.
        """
        if all(v is None for v in [
            self.weight, self.reps, self.duration_seconds, self.distance_meters
        ]):
            raise ValueError(
                "A set must have at least one measurement: "
                "weight, reps, duration, or distance"
            )
        return self
```

---

## iOS / Swift Patterns

### Complete SwiftUI View with ViewModel

```swift
// WorkoutSetRowView.swift
// PRLifts iOS App
//
// Displays a single workout set row in the ActiveWorkoutScreen.
// All business logic lives in the ViewModel — the View only displays.

import SwiftUI

struct WorkoutSetRowView: View {

    let viewModel: WorkoutSetRowViewModel

    var body: some View {
        HStack(spacing: PRSpacing.small) {

            // Set number
            Text("#\(viewModel.setNumber)")
                .font(.prDataSmall)
                .foregroundColor(.prTextSecondary)
                .frame(width: 24, alignment: .leading)
                .accessibilityHidden(true)  // combined with row label

            // Weight and reps
            VStack(alignment: .leading, spacing: PRSpacing.xxxSmall) {
                Text(viewModel.primaryMetric)
                    .font(.prDataMedium)
                    .foregroundColor(.prTextPrimary)

                if let secondaryMetric = viewModel.secondaryMetric {
                    Text(secondaryMetric)
                        .font(.prBodySecondary)
                        .foregroundColor(.prTextSecondary)
                }
            }

            Spacer()

            // PR indicator
            if viewModel.isPersonalRecord {
                Image(systemName: "star.fill")
                    .foregroundColor(.prAccent)
                    .accessibilityHidden(true)  // PR status is in the row label
            }
        }
        .padding(.vertical, PRSpacing.xxSmall)
        .accessibilityElement(children: .combine)
        .accessibilityLabel(viewModel.accessibilityLabel)
    }
}
```

```swift
// WorkoutSetRowViewModel.swift
// PRLifts iOS App
//
// ViewModel for WorkoutSetRowView. No SwiftUI imports —
// this is plain Swift and can be unit tested directly.

struct WorkoutSetRowViewModel {

    private let set: WorkoutSet
    private let unitPreference: WeightUnit

    init(set: WorkoutSet, unitPreference: WeightUnit) {
        self.set = set
        self.unitPreference = unitPreference
    }

    var setNumber: Int { set.setNumber }

    var isPersonalRecord: Bool { set.setType == .pr }

    // Format: "225 lbs × 5" or "BW × 10" or "32:15"
    var primaryMetric: String {
        if let weight = set.weight {
            let converted = convertWeight(weight, from: set.weightUnit, to: unitPreference)
            let unit = unitPreference.abbreviation
            if let reps = set.reps {
                return "\(formatted(converted)) \(unit) × \(reps)"
            }
            return "\(formatted(converted)) \(unit)"
        } else if let reps = set.reps {
            return "BW × \(reps)"
        } else if let duration = set.durationSeconds {
            return format(seconds: duration)
        }
        return "—"
    }

    var secondaryMetric: String? {
        guard let rpe = set.rpe else { return nil }
        return "RPE \(rpe)"
    }

    var accessibilityLabel: String {
        var parts = ["Set \(setNumber)", primaryMetric]
        if let secondary = secondaryMetric { parts.append(secondary) }
        if isPersonalRecord { parts.append("Personal record") }
        return parts.joined(separator: ", ")
    }

    // MARK: - Private helpers

    private func convertWeight(_ weight: Double, from: WeightUnit?, to: WeightUnit) -> Double {
        guard let from else { return weight }
        guard from != to else { return weight }
        return from == .kg ? weight * 2.20462 : weight / 2.20462
    }

    private func formatted(_ value: Double) -> String {
        value.truncatingRemainder(dividingBy: 1) == 0
            ? String(Int(value))
            : String(format: "%.1f", value)
    }

    private func format(seconds: Int) -> String {
        let minutes = seconds / 60
        let secs = seconds % 60
        return String(format: "%d:%02d", minutes, secs)
    }
}
```

---

### Complete XCTest with Stubs

```swift
// WorkoutSetRowViewModelTests.swift
// PRLifts Core Library Tests

import XCTest
@testable import PRLiftsCore

final class WorkoutSetRowViewModelTests: XCTestCase {

    // MARK: - Primary Metric

    func test_primaryMetric_showsWeightAndReps_forStandardSet() {
        // Arrange
        let set = WorkoutSet.stub(weight: 225, weightUnit: .lbs, reps: 5)
        let sut = WorkoutSetRowViewModel(set: set, unitPreference: .lbs)

        // Act
        let result = sut.primaryMetric

        // Assert
        XCTAssertEqual(result, "225 lbs × 5")
    }

    func test_primaryMetric_convertsToKg_whenUnitPreferenceIsKg() {
        // Arrange
        let set = WorkoutSet.stub(weight: 225, weightUnit: .lbs, reps: 5)
        let sut = WorkoutSetRowViewModel(set: set, unitPreference: .kg)

        // Act
        let result = sut.primaryMetric

        // Assert
        // 225 lbs ≈ 102.1 kg
        XCTAssertTrue(result.hasPrefix("102.1 kg"))
    }

    func test_primaryMetric_showsBW_forBodyweightSet() {
        // Arrange
        let set = WorkoutSet.stubBodyweight(reps: 12)
        let sut = WorkoutSetRowViewModel(set: set, unitPreference: .lbs)

        // Act / Assert
        XCTAssertEqual(sut.primaryMetric, "BW × 12")
    }

    func test_primaryMetric_formatsTime_forCardioSet() {
        // Arrange
        let set = WorkoutSet.stubCardio(distanceMeters: 5000, durationSeconds: 1800)
        let sut = WorkoutSetRowViewModel(set: set, unitPreference: .lbs)

        // Act / Assert
        XCTAssertEqual(sut.primaryMetric, "30:00")
    }

    // MARK: - Accessibility

    func test_accessibilityLabel_includesPRStatus_forPersonalRecord() {
        // Arrange
        let set = WorkoutSet.stub(weight: 225, reps: 5, setType: .pr)
        let sut = WorkoutSetRowViewModel(set: set, unitPreference: .lbs)

        // Act
        let label = sut.accessibilityLabel

        // Assert
        XCTAssertTrue(label.contains("Personal record"),
                      "Accessibility label should announce PR status")
    }
}
```

---

## Shared Patterns

### Correlation ID Middleware (Backend)

```python
# middleware/correlation_id.py

import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Assigns a correlation_id UUID to every request.
    Stored in request.state.correlation_id.
    Returned in X-Correlation-ID response header.
    All log statements must include this ID.
    """

    async def dispatch(self, request: Request, call_next):
        correlation_id = uuid.uuid4()
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = str(correlation_id)
        return response
```

---

### Deep Link Handling (iOS)

See DEEP_LINKS.md for the complete `DeepLinkRouter` implementation.
The pattern: URL arrives → `DeepLinkRouter.shared.handle(url)` → published `destination` property → root view navigates.

---

### Feature Flag Check (iOS)

```swift
// PostHog feature flag check with beta_tier fallback
func isFeatureEnabled(_ flag: FeatureFlag, for user: User) -> Bool {
    // Check PostHog first
    if let posthogResult = PostHog.shared.isFeatureEnabled(flag.rawValue) {
        return posthogResult
    }
    // Fallback to beta_tier if PostHog is unavailable
    return user.betaTier == .fullAccess
}
```

