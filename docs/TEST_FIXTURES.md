# PRLifts — Test Fixture Library

**Version:** 1.0
**Last updated:** April 2026
**Owner:** QA Standards Lead
**Audience:** All developers (human and Claude Code)

> Test fixtures are the stub factories and test data that make tests
> readable and resilient. Every model has a stub factory. Tests only set
> the fields they care about — everything else uses sensible defaults.
> This prevents tests from breaking when a new required field is added.

---

## Principles

1. **Stubs have sensible defaults.** A test for PR detection should not
   need to set `is_completed`, `workout_exercise_id`, or `set_number` —
   only `weight` and `reps`.

2. **Stubs live in TestSupport.** Never in production code.

3. **No real user data.** Ever. In any test fixture.

4. **No hardcoded UUIDs.** Use `UUID()` for random IDs or named constants
   for IDs that need to be stable across tests.

---

## Swift — Core Library Test Fixtures

### File Location

```
core-library/
  Tests/
    TestSupport/
      Stubs/
        WorkoutSet+Stub.swift
        Workout+Stub.swift
        Exercise+Stub.swift
        PersonalRecord+Stub.swift
        User+Stub.swift
        Job+Stub.swift
```

### WorkoutSet+Stub.swift

```swift
// WorkoutSet+Stub.swift
// PRLifts Core Library — TestSupport
//
// Stub factory for WorkoutSet. Tests only set fields they care about.
// All other fields use production-realistic defaults.

#if DEBUG

extension WorkoutSet {

    /// Creates a WorkoutSet with sensible defaults for testing.
    ///
    /// Only override the fields your test actually cares about.
    /// Example: WorkoutSet.stub(weight: 100, reps: 5)
    static func stub(
        id: UUID = UUID(),
        workoutExerciseID: UUID = UUID(),
        setNumber: Int = 1,
        setType: SetType = .normal,
        weight: Double? = 100,
        weightUnit: WeightUnit = .lbs,
        weightModifier: WeightModifier = .none,
        modifierValue: Double? = nil,
        modifierUnit: WeightUnit? = nil,
        reps: Int? = 5,
        durationSeconds: Int? = nil,
        distanceMeters: Double? = nil,
        calories: Int? = nil,
        rpe: Int? = nil,
        isCompleted: Bool = true,
        notes: String? = nil,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) -> WorkoutSet {
        WorkoutSet(
            id: id,
            workoutExerciseID: workoutExerciseID,
            setNumber: setNumber,
            setType: setType,
            weight: weight,
            weightUnit: weightUnit,
            weightModifier: weightModifier,
            modifierValue: modifierValue,
            modifierUnit: modifierUnit,
            reps: reps,
            durationSeconds: durationSeconds,
            distanceMeters: distanceMeters,
            calories: calories,
            rpe: rpe,
            isCompleted: isCompleted,
            notes: notes,
            createdAt: createdAt,
            updatedAt: updatedAt
        )
    }

    // ── Convenience factories for common test scenarios ─────────────────

    /// A heavy barbell set approaching failure.
    static func stubHeavy() -> WorkoutSet {
        stub(weight: 225, weightUnit: .lbs, reps: 3, rpe: 9)
    }

    /// A light warmup set.
    static func stubWarmup() -> WorkoutSet {
        stub(weight: 95, weightUnit: .lbs, reps: 10, setType: .warmup, rpe: 3)
    }

    /// A pure bodyweight set (e.g., pull-up with no modifier).
    static func stubBodyweight(reps: Int = 10) -> WorkoutSet {
        stub(weight: nil, weightUnit: nil, weightModifier: .none, reps: reps)
    }

    /// A weighted bodyweight set (e.g., weighted pull-up).
    static func stubWeighted(addedWeight: Double = 25, reps: Int = 8) -> WorkoutSet {
        stub(
            weight: nil,
            weightUnit: nil,
            weightModifier: .weighted,
            modifierValue: addedWeight,
            modifierUnit: .lbs,
            reps: reps
        )
    }

    /// A cardio set (e.g., 5k run).
    static func stubCardio(distanceMeters: Double = 5000, durationSeconds: Int = 1800) -> WorkoutSet {
        stub(weight: nil, weightUnit: nil, reps: nil,
             durationSeconds: durationSeconds,
             distanceMeters: distanceMeters)
    }
}

#endif
```

### Exercise+Stub.swift

```swift
// Exercise+Stub.swift
// PRLifts Core Library — TestSupport

#if DEBUG

extension Exercise {

    static func stub(
        id: UUID = UUID(),
        name: String = "Test Exercise",
        category: ExerciseCategory = .strength,
        muscleGroup: MuscleGroup = .midChest,
        secondaryMuscleGroups: [MuscleGroup]? = nil,
        equipment: ExerciseEquipment = .barbell,
        isCustom: Bool = false,
        createdBy: UUID? = nil
    ) -> Exercise {
        Exercise(
            id: id,
            name: name,
            category: category,
            muscleGroup: muscleGroup,
            secondaryMuscleGroups: secondaryMuscleGroups,
            equipment: equipment,
            instructions: nil,
            demoURL: nil,
            isCustom: isCustom,
            createdBy: createdBy,
            createdAt: Date(),
            updatedAt: Date()
        )
    }

    // ── Named stubs for tests that need specific exercises ───────────────

    /// Standard barbell bench press. Use when exercise identity matters.
    static var benchPress: Exercise {
        stub(name: "Bench Press", category: .strength,
             muscleGroup: .midChest,
             secondaryMuscleGroups: [.shoulders, .triceps],
             equipment: .barbell)
    }

    /// Standard barbell squat.
    static var squat: Exercise {
        stub(name: "Barbell Squat", category: .strength,
             muscleGroup: .quads,
             secondaryMuscleGroups: [.hamstrings, .glutes],
             equipment: .barbell)
    }

    /// Bodyweight pull-up.
    static var pullUp: Exercise {
        stub(name: "Pull-up", category: .strength,
             muscleGroup: .upperBack,
             secondaryMuscleGroups: [.biceps],
             equipment: .bodyweight)
    }

    /// Treadmill run (cardio).
    static var treadmillRun: Exercise {
        stub(name: "Running", category: .cardio,
             muscleGroup: .fullBody,
             equipment: .cardioMachine)
    }
}

#endif
```

### PersonalRecord+Stub.swift

```swift
// PersonalRecord+Stub.swift
// PRLifts Core Library — TestSupport

#if DEBUG

extension PersonalRecord {

    static func stub(
        id: UUID = UUID(),
        userID: UUID = UUID(),
        exerciseID: UUID = UUID(),
        workoutSetID: UUID = UUID(),
        weightModifier: WeightModifier = .none,
        recordType: RecordType = .heaviestWeight,
        value: Double = 225,
        valueUnit: ValueUnit = .lbs,
        recordedAt: Date = Date(),
        previousValue: Double? = 215,
        previousRecordedAt: Date? = Calendar.current.date(
            byAdding: .day, value: -14, to: Date()
        )
    ) -> PersonalRecord {
        PersonalRecord(
            id: id,
            userID: userID,
            exerciseID: exerciseID,
            workoutSetID: workoutSetID,
            weightModifier: weightModifier,
            recordType: recordType,
            value: value,
            valueUnit: valueUnit,
            recordedAt: recordedAt,
            previousValue: previousValue,
            previousRecordedAt: previousRecordedAt,
            createdAt: Date(),
            updatedAt: Date()
        )
    }
}

#endif
```

### User+Stub.swift

```swift
// User+Stub.swift
// PRLifts Core Library — TestSupport

#if DEBUG

extension User {

    static func stub(
        id: UUID = UUID(),
        email: String? = nil,              // nullable by default — realistic
        displayName: String? = "Test User",
        unitPreference: WeightUnit = .lbs,
        measurementUnit: MeasurementUnit = .cm,
        gender: Gender = .na,
        goal: UserGoal? = .buildMuscle,
        betaTier: BetaTier = .none
    ) -> User {
        User(
            id: id,
            email: email,
            displayName: displayName,
            avatarURL: nil,
            unitPreference: unitPreference,
            measurementUnit: measurementUnit,
            dateOfBirth: nil,
            gender: gender,
            goal: goal,
            betaTier: betaTier,
            createdAt: Date(),
            updatedAt: Date()
        )
    }
}

#endif
```

### Job+Stub.swift

```swift
// Job+Stub.swift
// PRLifts Core Library — TestSupport

#if DEBUG

extension Job {

    static func stub(
        id: UUID = UUID(),
        userID: UUID = UUID(),
        jobType: JobType = .insight,
        status: JobStatus = .pending,
        result: JobResult? = nil,
        errorMessage: String? = nil,
        createdAt: Date = Date(),
        expiresAt: Date = Calendar.current.date(
            byAdding: .minute, value: 5, to: Date()
        )!
    ) -> Job {
        Job(
            id: id,
            userID: userID,
            jobType: jobType,
            status: status,
            result: result,
            errorMessage: errorMessage,
            createdAt: createdAt,
            startedAt: nil,
            completedAt: nil,
            expiresAt: expiresAt
        )
    }

    /// A job that has already expired.
    static func stubExpired() -> Job {
        stub(
            status: .expired,
            errorMessage: "This request took too long. Please try again.",
            expiresAt: Calendar.current.date(byAdding: .minute, value: -1, to: Date())!
        )
    }

    /// A completed insight job.
    static func stubCompletedInsight(text: String = "Great workout!") -> Job {
        stub(
            jobType: .insight,
            status: .complete,
            result: .insight(InsightJobResult(insightText: text))
        )
    }

    /// A failed future self job (quality gate failure).
    static func stubQualityGateFailed() -> Job {
        stub(
            jobType: .futureSelf,
            status: .failed,
            errorMessage: "Your vision is being crafted — check back soon"
        )
    }
}

#endif
```

---

## Python — Backend Test Fixtures

### File Location

```
backend/
  tests/
    fixtures/
      __init__.py
      workout_fixtures.py
      exercise_fixtures.py
      user_fixtures.py
      job_fixtures.py
```

### user_fixtures.py

```python
# user_fixtures.py
# PRLifts Backend — Test Fixtures
#
# Factory functions for User test data.
# Use these in pytest fixtures — never construct models directly in tests.

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.models import User, WeightUnit, MeasurementUnit, Gender, UserGoal, BetaTier


def make_user(
    id=None,
    email=None,                          # nullable — realistic default
    display_name="Test User",
    unit_preference=WeightUnit.lbs,
    measurement_unit=MeasurementUnit.cm,
    gender=Gender.na,
    goal=UserGoal.build_muscle,
    beta_tier=BetaTier.none,
) -> User:
    """
    Creates a User with sensible defaults for testing.
    Only override the fields your test actually cares about.
    """
    return User(
        id=id or uuid4(),
        email=email,
        display_name=display_name,
        avatar_url=None,
        unit_preference=unit_preference,
        measurement_unit=measurement_unit,
        date_of_birth=None,
        gender=gender,
        goal=goal,
        beta_tier=beta_tier,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def test_user(db_session):
    """Standard test user saved to the test database."""
    user = make_user()
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def full_access_user(db_session):
    """User with full beta access — for testing premium features."""
    user = make_user(beta_tier=BetaTier.full_access)
    db_session.add(user)
    db_session.commit()
    return user
```

### workout_fixtures.py

```python
# workout_fixtures.py
# PRLifts Backend — Test Fixtures

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.models import (
    Workout, WorkoutExercise, WorkoutSet,
    WorkoutStatus, WorkoutType, WorkoutFormat,
    SetType, WeightModifier, WeightUnit
)


def make_workout(
    user_id=None,
    status=WorkoutStatus.in_progress,
    type=WorkoutType.ad_hoc,
    format=WorkoutFormat.weightlifting,
    name=None,
    started_at=None,
) -> Workout:
    return Workout(
        id=uuid4(),
        user_id=user_id or uuid4(),
        name=name,
        notes=None,
        status=status,
        type=type,
        format=format,
        plan_id=None,
        started_at=started_at or datetime.now(timezone.utc),
        completed_at=None,
        duration_seconds=None,
        location=None,
        rating=None,
        server_received_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def make_workout_set(
    workout_exercise_id=None,
    set_number=1,
    set_type=SetType.normal,
    weight=100.0,
    weight_unit=WeightUnit.lbs,
    weight_modifier=WeightModifier.none,
    modifier_value=None,
    modifier_unit=None,
    reps=5,
    duration_seconds=None,
    distance_meters=None,
    rpe=None,
    is_completed=True,
) -> WorkoutSet:
    return WorkoutSet(
        id=uuid4(),
        workout_exercise_id=workout_exercise_id or uuid4(),
        set_number=set_number,
        set_type=set_type,
        weight=weight,
        weight_unit=weight_unit,
        weight_modifier=weight_modifier,
        modifier_value=modifier_value,
        modifier_unit=modifier_unit,
        reps=reps,
        duration_seconds=duration_seconds,
        distance_meters=distance_meters,
        calories=None,
        rpe=rpe,
        is_completed=is_completed,
        notes=None,
        server_received_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def make_workout_set_bodyweight(reps=10) -> WorkoutSet:
    """Pure bodyweight set (pull-up, push-up, etc.)."""
    return make_workout_set(
        weight=None, weight_unit=None,
        weight_modifier=WeightModifier.none,
        reps=reps
    )


def make_workout_set_weighted_bodyweight(added_weight=25.0, reps=8) -> WorkoutSet:
    """Weighted bodyweight set (weighted pull-up, dip with belt, etc.)."""
    return make_workout_set(
        weight=None, weight_unit=None,
        weight_modifier=WeightModifier.weighted,
        modifier_value=added_weight, modifier_unit=WeightUnit.lbs,
        reps=reps
    )
```

### job_fixtures.py

```python
# job_fixtures.py
# PRLifts Backend — Test Fixtures

import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from app.models import Job, JobType, JobStatus


def make_job(
    user_id=None,
    job_type=JobType.insight,
    status=JobStatus.pending,
    result=None,
    error_message=None,
    expires_at=None,
) -> Job:
    now = datetime.now(timezone.utc)
    return Job(
        id=uuid4(),
        user_id=user_id or uuid4(),
        job_type=job_type,
        status=status,
        result=result,
        error_message=error_message,
        created_at=now,
        started_at=None,
        completed_at=None,
        expires_at=expires_at or (now + timedelta(minutes=5)),
    )


def make_expired_job(user_id=None) -> Job:
    """A job that has already passed its TTL."""
    now = datetime.now(timezone.utc)
    return make_job(
        user_id=user_id,
        status=JobStatus.pending,        # not yet cleaned up
        expires_at=now - timedelta(minutes=1)  # already past
    )


def make_completed_insight_job(user_id=None, insight_text="Great workout!") -> Job:
    return make_job(
        user_id=user_id,
        job_type=JobType.insight,
        status=JobStatus.complete,
        result={"insight_text": insight_text}
    )


def make_failed_quality_gate_job(user_id=None) -> Job:
    return make_job(
        user_id=user_id,
        job_type=JobType.future_self,
        status=JobStatus.failed,
        error_message="Your vision is being crafted — check back soon"
    )


@pytest.fixture
def pending_insight_job(db_session, test_user):
    job = make_job(user_id=test_user.id, job_type=JobType.insight)
    db_session.add(job)
    db_session.commit()
    return job


@pytest.fixture
def expired_job(db_session, test_user):
    job = make_expired_job(user_id=test_user.id)
    db_session.add(job)
    db_session.commit()
    return job
```

---

## Named Constants for Stable Test IDs

When a test needs to reference the same UUID across multiple assertions,
use named constants rather than hardcoded UUID strings:

```swift
// Swift
enum TestConstants {
    static let knownUserID = UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
    static let knownWorkoutID = UUID(uuidString: "00000000-0000-0000-0000-000000000002")!
    static let knownExerciseID = UUID(uuidString: "00000000-0000-0000-0000-000000000003")!
}
```

```python
# Python
from uuid import UUID
KNOWN_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
KNOWN_WORKOUT_ID = UUID("00000000-0000-0000-0000-000000000002")
KNOWN_EXERCISE_ID = UUID("00000000-0000-0000-0000-000000000003")
```

These IDs are test-only. They must never appear in seed data or production data.

