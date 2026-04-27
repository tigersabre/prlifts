# PRLifts — Glossary

**Version:** 1.0
**Last updated:** April 2026
**Owners:** Staff/Principal Engineer + all domain leads
**Audience:** All developers (human and Claude Code)

> This is the single source of truth for terminology across the entire codebase.
> When a term is used in code, documentation, or conversation, it must match this glossary.
> If a term is not here and you need to introduce one, add it here first.

---

## Why This Document Exists

Inconsistent naming is one of the most common causes of bugs and miscommunication
in a codebase. If one file calls it a "session" and another calls it a "workout",
the reader cannot tell if they are the same thing. They might not be. This glossary
eliminates that ambiguity.

---

## Core Domain Terms

### Workout
A single training session performed by a user. Contains one or more WorkoutExercises.
Can be ad hoc (unplanned) or planned (linked to a WorkoutPlan). Has a lifecycle:
`in_progress` → `paused` → `completed` or `partial_completion`.

**In code:** `Workout` (Swift model), `Workout` (Python SQLAlchemy model), `workout` (PostgreSQL table)
**Not:** "session", "training", "gym visit", "lift"

### WorkoutExercise
A specific exercise performed within a Workout, in a specific order. The junction
between a Workout and an Exercise. Contains one or more WorkoutSets.

**In code:** `WorkoutExercise` (Swift), `WorkoutExercise` (Python), `workout_exercise` (PostgreSQL)
**Not:** "exercise entry", "lift", "movement"

### WorkoutSet
A single set performed within a WorkoutExercise. The atomic unit of workout data.
Contains the actual numbers: weight, reps, duration, distance, RPE.

**In code:** `WorkoutSet` (Swift), `WorkoutSet` (Python), `workout_set` (PostgreSQL)
**Not:** "set entry", "rep", "attempt"

### Exercise
A definition of a movement. "Bench Press", "5k Run", "Plank". Shared across all
users — not owned by any individual. Can come from ExerciseDB (canonical) or be
user-created (custom).

**In code:** `Exercise` (Swift), `Exercise` (Python), `exercise` (PostgreSQL)
**Not:** "movement", "lift", "activity"

### PersonalRecord (PR)
A user's best performance on a specific Exercise, for a specific RecordType and
WeightModifier combination. System-generated — never created manually by the user.
Stores both the current record value and the previous record value.

**In code:** `PersonalRecord` (Swift), `PersonalRecord` (Python), `personal_record` (PostgreSQL)
**Abbreviation in code:** `pr` is acceptable in variable names when unambiguous: `let prDetected = true`
**Not:** "best", "record", "high score", "achievement"

### RecordType
The dimension along which a PersonalRecord is measured. Values:
- `heaviest_weight` — maximum weight lifted
- `most_reps` — maximum reps at any weight
- `longest_duration` — longest time held/sustained
- `longest_distance` — greatest distance covered
- `best_rpe` — same weight achieved at lower RPE (getting easier)

**In code:** `RecordType` (Swift enum), `record_type` (Python/PostgreSQL)

### WeightModifier
How bodyweight exercises are classified. Values:
- `none` — pure bodyweight (no added load, no assistance)
- `assisted` — machine or band assistance reduces effective load
- `weighted` — added external load increases effective load

A weighted pull-up and a bodyweight pull-up are tracked as separate PersonalRecords
using the same Exercise. The WeightModifier is part of the PR key.

**In code:** `WeightModifier` (Swift enum), `weight_modifier` (Python/PostgreSQL)

### WorkoutPlan (V2)
A structured multi-week training program. Contains WorkoutPlanDays which contain
WorkoutPlanExercises. The plan is the *prescription* — the Workout is the *actuals*.

**In code:** `WorkoutPlan` (Swift), `WorkoutPlan` (Python), `workout_plan` (PostgreSQL)
**Not:** "program", "routine", "schedule"

### RPE
Rate of Perceived Exertion. A 1–10 scale representing how hard a set felt.
1 = trivially easy, 10 = maximum effort. Stored as an integer on WorkoutSet.

**In code:** `rpe` (always lowercase, always the abbreviation — never spelled out in code)

### Goal
A user's stated fitness objective. Collected during Phase 2 onboarding. Used to
drive the future self image generation prompt. Values:
- `build_muscle`
- `lose_fat`
- `improve_endurance`
- `athletic_performance`
- `general_fitness`

**In code:** `goal` (Swift property, Python column, PostgreSQL column)

---

## AI and Job Terms

### Job
An async AI operation tracked in the database. Created when a client requests an
AI operation, completed or expired asynchronously. The client polls for its status.

**In code:** `Job` (Swift model for polling), `Job` (Python SQLAlchemy), `job` (PostgreSQL)
**Not:** "task", "request", "operation", "async call"

### JobType
The category of AI operation a Job performs. Values:
- `insight` — workout insight generation via Claude API
- `future_self` — future self image generation via Fal.ai
- `benchmarking` — comparative performance analysis via Claude API

**In code:** `JobType` (Swift enum), `job_type` (Python/PostgreSQL)

### PromptTemplate
A versioned AI prompt stored in the database. One PromptTemplate is active per
feature at any time. Prompts are never hardcoded in application code.

**In code:** `PromptTemplate` (Python SQLAlchemy), `prompt_template` (PostgreSQL)
**Not:** "prompt", "system prompt", "AI instruction"

### QualityScore
The face similarity score assigned by Claude vision to a Fal.ai generated image.
Scale 1–10. Images scoring below 6 are not shown to the user.

**In code:** `qualityScore` (Swift), `quality_score` (Python/PostgreSQL)

### FutureSelf
The AI-generated image of the user looking fit and healthy, produced during
Phase 2 onboarding and used in show-up nudge notifications.

**In code:** `futureSelfImageURL` (Swift property), `future_self_image_url` (Python/PostgreSQL)
**Not:** "avatar", "generated photo", "AI photo", "vision image"

---

## Sync and Persistence Terms

### SyncEventLog
A device-side record of every SwiftData write, sync attempt, conflict resolution,
and sync outcome. Used for debugging offline sync issues.

**In code:** `SyncEventLog` (Swift SwiftData model), `sync_event_log` (PostgreSQL — uploaded copy)
**Not:** "sync log", "event log", "debug log"

### SyncTrigger
The event that initiates a sync of pending local data to the backend. Defined triggers:
app foreground, NWPathMonitor connectivity-restored, BGAppRefreshTask (opportunistic),
force-quit recovery on next launch.

**In code:** no single type — described in documentation and in sync service logic

### ConflictResolution
The mechanism for resolving conflicting writes between local SwiftData and the backend.
PRLifts uses last-write-wins based on `server_received_at` timestamp. Client
`client_created_at` is stored for context only.

**In documentation:** "conflict resolution" (lowercase, two words)

---

## Infrastructure Terms

### CorrelationID
A UUID generated per HTTP request, included in every log line for that request,
returned in the `X-Correlation-ID` response header. The primary support diagnostic tool.

**In code:** `correlation_id` (Python middleware), `X-Correlation-ID` (HTTP header)
**Not:** "request ID", "trace ID", "log ID"

### Job Expiry
The automatic failure of a Job that has not reached a terminal state within 5 minutes.
The APScheduler cleanup task sets expired jobs to status `expired` every 60 seconds.

**In documentation:** "job expiry" or "expired job" (never "job timeout" or "hung job")

### FeatureFlag
A PostHog-managed boolean that controls access to a feature per user or cohort.
Two-layer access: PostHog flag checked first, `beta_tier` on User as fallback.

**In code:** evaluated via PostHog SDK — never hardcoded conditionals
**Not:** "feature toggle", "flag", "switch"

---

## Onboarding Terms

### Phase 1 Onboarding
The required 4-step onboarding flow completed before a user logs their first workout.
Steps: Welcome, Sign in, Display name, Units.

**In documentation:** "Phase 1 onboarding" or "Phase 1"

### Phase 2 Onboarding
The optional progressive disclosure flow triggered after a user completes their first
workout. Introduces the future self feature, collects goal and demographics, requests
notification permission.

**In documentation:** "Phase 2 onboarding" or "Phase 2"

### BiometricConsent
The explicit written consent a user provides before their photo is processed for
future self generation. A BiometricConsent record is created in the database as a
legal audit record before any photo is sent to Fal.ai.

**In code:** `BiometricConsent` (Python SQLAlchemy), `biometric_consent` (PostgreSQL)
**Not:** "photo consent", "image consent", "consent"

---

## User and Access Terms

### BetaTier
The database-level access control tier for a user. Values: `none` (default), `tester`,
`full_access`. Checked as a fallback when PostHog is unavailable.

**In code:** `betaTier` (Swift), `beta_tier` (Python/PostgreSQL)

### AnonymousUserID
The UUID used to identify a user in logs, analytics, and support contexts. Never the
user's email or name. The `id` field on the User entity.

**In documentation:** "anonymous user ID" — always clarify this is not the email

---

## Terms Deliberately Not Used

These terms are ambiguous in the PRLifts context and must not appear in code or documentation:

| Avoid | Use instead |
|---|---|
| session | workout |
| lift | exercise or workout_set depending on context |
| training | workout or workout_plan |
| record | personal_record |
| task | job |
| request (for async AI) | job |
| prompt | prompt_template |
| timeout (for jobs) | job expiry |
| avatar | future_self |
| photo | user_photo (before processing) or future_self_image_url (after) |

