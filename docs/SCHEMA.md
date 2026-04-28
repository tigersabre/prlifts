# PRLifts — Database Schema Reference

**Version:** 1.0
**Last updated:** April 2026
**Owner:** Data Architect
**Audience:** All developers (human and Claude Code)

> This document is the authoritative reference for the PostgreSQL schema.
> It is prose-first for human readability with exact SQL for implementation.
> The actual migration files in `backend/migrations/` are the deployed source
> of truth — this document and those files must stay in sync.
> If they conflict, the migration files win and this document must be updated.

---

## Conventions (from DATA_STANDARDS.md)

- Tables: `snake_case` singular nouns
- Columns: `snake_case`, booleans prefixed `is_` or `has_`
- Foreign keys: `{referenced_table}_id`
- Timestamps: always UTC, always `created_at` + `updated_at`
- Every table has a `COMMENT ON TABLE` before migration merges
- Every migration has `up` and `down` scripts

---

## Extensions Required

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- for fuzzy text search on exercise names
```

---

## Enums

```sql
-- Weight units
CREATE TYPE weight_unit AS ENUM ('kg', 'lbs');

-- Measurement units (display preference — storage always cm)
CREATE TYPE measurement_unit AS ENUM ('cm', 'inches');

-- Gender options
CREATE TYPE gender AS ENUM ('male', 'female', 'na');

-- User fitness goal
CREATE TYPE user_goal AS ENUM (
    'build_muscle',
    'lose_fat',
    'improve_endurance',
    'athletic_performance',
    'general_fitness'
);

-- User beta access tier
CREATE TYPE beta_tier AS ENUM ('none', 'tester', 'full_access');

-- Workout lifecycle status
CREATE TYPE workout_status AS ENUM (
    'in_progress',
    'paused',
    'partial_completion',
    'completed'
);

-- Whether workout follows a plan or is ad hoc
CREATE TYPE workout_type AS ENUM ('ad_hoc', 'planned');

-- Primary movement format of a workout
CREATE TYPE workout_format AS ENUM ('weightlifting', 'cardio', 'mixed', 'other');

-- Where the workout took place
CREATE TYPE workout_location AS ENUM ('gym', 'home', 'outdoor', 'other');

-- Classification of a set within a workout
CREATE TYPE set_type AS ENUM ('normal', 'warmup', 'dropset', 'failure', 'pr');

-- How bodyweight is modified for a set
CREATE TYPE weight_modifier AS ENUM ('none', 'assisted', 'weighted');

-- The dimension along which a PR is measured
CREATE TYPE record_type AS ENUM (
    'heaviest_weight',
    'most_reps',
    'longest_duration',
    'longest_distance',
    'best_rpe'
);

-- Units for PR values
CREATE TYPE value_unit AS ENUM ('kg', 'lbs', 'reps', 'seconds', 'meters');

-- Exercise primary category
-- NOTE: flagged for V2 lookup table migration (high-change enum)
CREATE TYPE exercise_category AS ENUM (
    'strength', 'cardio', 'flexibility', 'bodyweight',
    'mobility', 'saq', 'rehab'
);

-- Exercise equipment requirement
-- NOTE: flagged for V2 lookup table migration (high-change enum)
CREATE TYPE exercise_equipment AS ENUM (
    'barbell', 'dumbbell', 'kettlebell', 'machine',
    'cable', 'bodyweight', 'cardio_machine', 'other'
);

-- Muscle group targeted by an exercise
-- NOTE: flagged for V2 lookup table migration (high-change enum)
CREATE TYPE muscle_group AS ENUM (
    'upper_chest', 'mid_chest', 'lower_chest',
    'upper_back', 'lower_back',
    'shoulders', 'biceps', 'triceps',
    'quads', 'hamstrings', 'calves', 'glutes',
    'abs', 'obliques', 'full_body'
);

-- Async AI job status
CREATE TYPE job_status AS ENUM (
    'pending', 'processing', 'complete', 'failed', 'expired'
);

-- Async AI job category
CREATE TYPE job_type AS ENUM ('insight', 'future_self', 'benchmarking');

-- Sync event categories for debugging
CREATE TYPE sync_event_type AS ENUM (
    'write_attempt', 'sync_attempt', 'sync_success',
    'sync_failure', 'conflict_resolved'
);

-- Entities that can appear in sync log
CREATE TYPE sync_entity_type AS ENUM (
    'workout', 'workout_exercise', 'workout_set',
    'personal_record', 'body_metrics', 'steps_entry'
);
```

---

## Tables

### user

Stores all user accounts. The central entity of the system.

```sql
CREATE TABLE "user" (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email               TEXT UNIQUE,                     -- nullable: Apple Sign In may not provide
    display_name        TEXT,
    avatar_url          TEXT,
    unit_preference     weight_unit NOT NULL DEFAULT 'lbs',
    measurement_unit    measurement_unit NOT NULL DEFAULT 'cm',
    date_of_birth       DATE,
    gender              gender NOT NULL DEFAULT 'na',
    goal                user_goal,                       -- nullable: set in Phase 2 onboarding
    phase_2_completed_at TIMESTAMPTZ,                       -- null until Phase 2 onboarding complete
    beta_tier           beta_tier NOT NULL DEFAULT 'none',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE "user" IS
'All PRLifts user accounts. Central entity — every other user-owned table
references this via user_id with RLS policy user_id = auth.uid().
email is nullable because Apple Sign In may provide only a relay address or nothing.
goal is nullable — collected in Phase 2 onboarding, not required for core app.
measurement_unit is a display preference — all body measurements stored in cm.';

COMMENT ON COLUMN "user".goal IS
'User fitness objective. Drives the future self image generation prompt.
Nullable — users who skip Phase 2 onboarding may not have a goal set.
Required for future_self job creation.';

COMMENT ON COLUMN "user".phase_2_completed_at IS
'Timestamp when Phase 2 onboarding was completed. NULL means Phase 2 not yet done.
Used to determine whether to show Phase 2 prompt after first workout.
Set by the backend when the user completes NotificationPermissionScreen.';

COMMENT ON COLUMN "user".beta_tier IS
'Database-level feature access control. Fallback when PostHog is unavailable.
full_access grants all premium features regardless of PostHog flags.';
```

---

### exercise

Defines a movement. Shared across all users — not owned by any individual.

```sql
CREATE TABLE exercise (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    TEXT NOT NULL UNIQUE,
    category                exercise_category NOT NULL,
    muscle_group            muscle_group NOT NULL,
    secondary_muscle_groups muscle_group[],              -- PostgreSQL native array
    equipment               exercise_equipment NOT NULL,
    instructions            TEXT,
    demo_url                TEXT,                        -- ExerciseDB GIF/video URL
    is_custom               BOOLEAN NOT NULL DEFAULT FALSE,
    created_by              UUID REFERENCES "user"(id) ON DELETE SET NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE exercise IS
'Definitions of movements. Shared across all users — not user-owned.
is_custom = false AND created_by IS NULL: canonical ExerciseDB exercise.
is_custom = true AND created_by IS NOT NULL: user-created custom exercise.
category, muscle_group, and equipment are PostgreSQL enums in V1.
All three are flagged for migration to lookup tables in V2 before the
exercise library grows significantly — enums require migrations to extend.';

COMMENT ON COLUMN exercise.secondary_muscle_groups IS
'Additional muscle groups targeted beyond the primary muscle_group.
Uses PostgreSQL native array type — no junction table needed.
Example: bench press has muscle_group = mid_chest,
secondary_muscle_groups = ARRAY[shoulders, triceps].';
```

---

### workout

A single training event. Contains WorkoutExercises.

```sql
CREATE TABLE workout (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    name             TEXT,
    notes            TEXT,
    status           workout_status NOT NULL DEFAULT 'in_progress',
    type             workout_type NOT NULL,
    format           workout_format NOT NULL,
    plan_id          UUID,                               -- V2: will reference workout_plan
    started_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at     TIMESTAMPTZ,
    duration_seconds INTEGER,                            -- stored for query perf (derived)
    location         workout_location,
    rating           SMALLINT CHECK (rating BETWEEN 1 AND 5),
    server_received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), -- governs conflict resolution
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE workout IS
'A single training event. The container for WorkoutExercises and WorkoutSets.
status lifecycle: in_progress → paused → completed or partial_completion.
partial_completion distinguishes genuinely unfinished sessions from completed ones.
duration_seconds is derivable from completed_at - started_at but stored explicitly
for query performance on weekly volume and average workout duration calculations.
server_received_at is the authoritative timestamp for last-write-wins conflict
resolution — client-provided timestamps are never trusted for ordering.';
```

---

### workout_exercise

An exercise performed within a specific workout, in a specific order.
Junction between workout and exercise.

```sql
CREATE TABLE workout_exercise (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_id  UUID NOT NULL REFERENCES workout(id) ON DELETE CASCADE,
    exercise_id UUID NOT NULL REFERENCES exercise(id),
    order_index INTEGER NOT NULL,
    notes       TEXT,
    rest_seconds INTEGER CHECK (rest_seconds BETWEEN 0 AND 3600),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE workout_exercise IS
'Junction between a workout and an exercise. Represents one exercise
as performed in one workout, in a specific order. This is the prescription
context — the actual numbers are in workout_set.
order_index preserves the sequence exercises were performed.
rest_seconds is per-exercise (consistent across sets) — not per-set.
Notes here are workout-level observations about the movement as a whole.';
```

---

### workout_set

A single set within a workout exercise. The atomic unit of workout data.

```sql
CREATE TABLE workout_set (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_exercise_id  UUID NOT NULL REFERENCES workout_exercise(id) ON DELETE CASCADE,
    set_number           INTEGER NOT NULL CHECK (set_number BETWEEN 1 AND 100),
    set_type             set_type NOT NULL DEFAULT 'normal',
    weight               NUMERIC(8,2) CHECK (weight >= 0 AND weight <= 2000),
    weight_unit          weight_unit,
    weight_modifier      weight_modifier NOT NULL DEFAULT 'none',
    modifier_value       NUMERIC(8,2) CHECK (modifier_value >= 0 AND modifier_value <= 500),
    modifier_unit        weight_unit,
    reps                 INTEGER CHECK (reps >= 0 AND reps <= 1000),
    duration_seconds     INTEGER CHECK (duration_seconds >= 0 AND duration_seconds <= 86400),
    distance_meters      NUMERIC(10,2) CHECK (distance_meters >= 0 AND distance_meters <= 100000),
    calories             INTEGER CHECK (calories >= 0 AND calories <= 10000),
    rpe                  SMALLINT CHECK (rpe BETWEEN 1 AND 10),
    is_completed         BOOLEAN NOT NULL DEFAULT FALSE,
    notes                TEXT,
    server_received_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT must_have_metric
        CHECK (weight IS NOT NULL OR reps IS NOT NULL OR
               duration_seconds IS NOT NULL OR distance_meters IS NOT NULL)
);

COMMENT ON TABLE workout_set IS
'The atomic unit of workout data. A single set within a workout exercise.
weight_modifier handles bodyweight exercise variants:
  none = pure bodyweight (no external load)
  assisted = machine/band reduces effective load (modifier_value is assistance amount)
  weighted = added external load (modifier_value is added weight)
Weighted and bodyweight PRs are tracked separately using weight_modifier as part of the key.
weight_unit is stored per-set (not derived from user preference) so historical data
remains accurate if the user changes their unit preference later.
set_type = pr is system-set by PR detection — never manually set by the user.
is_completed supports V2 program builder where sets are pre-populated from a plan.
The must_have_metric constraint ensures at least one measurement is recorded.';

COMMENT ON COLUMN workout_set.rpe IS
'Rate of Perceived Exertion on a 1–10 scale. 1 = trivially easy, 10 = maximum effort.
Used by the AI feedback layer to contextualise performance relative to effort.
A set at 225lb RPE 6 vs 225lb RPE 10 tells a different story.';
```

---

### personal_record

A user's best performance on an exercise. System-generated — never user-created.

```sql
CREATE TABLE personal_record (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    exercise_id          UUID NOT NULL REFERENCES exercise(id),
    workout_set_id       UUID NOT NULL REFERENCES workout_set(id),
    weight_modifier      weight_modifier NOT NULL,
    record_type          record_type NOT NULL,
    value                NUMERIC(10,2) NOT NULL,
    value_unit           value_unit,
    recorded_at          TIMESTAMPTZ NOT NULL,
    previous_value       NUMERIC(10,2),
    previous_recorded_at TIMESTAMPTZ,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE personal_record IS
'A user''s best performance on a specific exercise, for a specific record_type
and weight_modifier combination. System-generated on WorkoutSet completion —
never created by the user directly.
weight_modifier is part of the composite key: a weighted pull-up PR and a
bodyweight pull-up PR are separate records for the same exercise.
previous_value and previous_recorded_at are denormalised here for AI feedback
performance — avoids a complex historical query on every PR notification.
The AI can immediately say "you beat your previous PR of X set N weeks ago"
without an additional query.';
```

---

### job

Tracks async AI operations. Client polls for status.

```sql
CREATE TABLE job (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    job_type     job_type NOT NULL,
    status       job_status NOT NULL DEFAULT 'pending',
    result       JSONB,
    error_message TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at   TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    expires_at   TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '5 minutes'
);

COMMENT ON TABLE job IS
'Async AI job tracking. Created when client requests an AI operation.
Client polls GET /v1/jobs/{id} with exponential backoff (2s initial,
10s ceiling, 15 attempts max).
expires_at is set to NOW() + 5 minutes on creation. APScheduler cleanup
task runs every 60 seconds and sets jobs past their expires_at to expired
status if they are still in pending or processing state.
result is JSONB — schema varies by job_type. See openapi.yaml for shape.
error_message is user-facing — never contains internal details.';
```

---

### prompt_template

Versioned AI prompts stored in the database. Never hardcoded in application code.

```sql
CREATE TABLE prompt_template (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature         TEXT NOT NULL CHECK (feature IN ('insight', 'future_self', 'benchmarking')),
    version         TEXT NOT NULL,
    prompt_text     TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deactivated_at  TIMESTAMPTZ
);

-- Enforces exactly one active prompt per feature while allowing unlimited
-- inactive versions. A table-level UNIQUE constraint would block multiple
-- inactive rows for the same feature; a partial index does not.
CREATE UNIQUE INDEX idx_one_active_per_feature
    ON prompt_template (feature)
    WHERE is_active = TRUE;

COMMENT ON TABLE prompt_template IS
'Versioned AI prompts stored in the database, not in application code.
Only one prompt per feature may be active at a time (enforced by partial
unique index on feature WHERE is_active = TRUE). Multiple inactive versions
per feature are allowed, enabling prompt history and rollback.
Changes to prompt templates require a content review before activation.
The active PromptTemplate is fetched at runtime — no code deployment needed
to iterate on prompts. Every AIRequestLog row references the prompt_template_id
used, enabling quality comparison across versions.';
```

---

### ai_request_log

Access-controlled record of AI calls for quality debugging. Not general observability.

```sql
CREATE TABLE ai_request_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    prompt_template_id  UUID REFERENCES prompt_template(id),
    job_id              UUID REFERENCES job(id),
    endpoint            TEXT NOT NULL,
    response            TEXT,
    model               TEXT NOT NULL,
    quality_score       NUMERIC(4,2) CHECK (quality_score BETWEEN 1 AND 10),
    duration_ms         INTEGER NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '30 days'
);

COMMENT ON TABLE ai_request_log IS
'Access-controlled audit log of AI provider calls. NOT general observability —
that is handled by Railway logs and Sentry. This table exists exclusively for
diagnosing AI quality issues: wrong insight tone, poor quality gate behaviour, etc.
30-day retention enforced by APScheduler task deleting rows where expires_at < NOW().
Access restricted to admin role via RLS — never accessible to user-facing APIs.
quality_score: face similarity score from Claude vision for future_self jobs.
NULL quality_score on a future_self job means the scoring call failed (fail-closed).
High null rate triggers Sentry alert.';
```

---

### biometric_consent

Legal audit record of user consent to biometric data processing.

```sql
CREATE TABLE biometric_consent (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
    consent_given       BOOLEAN NOT NULL,
    consent_timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- server-assigned
    consent_version     TEXT NOT NULL,
    policy_text_hash    TEXT NOT NULL,
    ip_country          TEXT,
    user_deleted_at     TIMESTAMPTZ,   -- set when account deleted; row purged 1 year after this
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE biometric_consent IS
'Legal audit record of user consent to biometric data processing for the
future self feature. Backend-write-only — no direct client writes via RLS.
Required (with consent_given = true) before any photo is processed.
consent_timestamp is server-assigned — never trust client timestamps for legal records.
policy_text_hash is SHA-256 of the exact consent text shown — tamper-evident proof
of what the user agreed to.
ip_country is analytics-only — BIPA applies to Illinois residents regardless of IP
location (VPN users still subject to BIPA). Do not use ip_country for BIPA scoping.
One record per consent event — multiple records if consent is revoked and re-given.
IMPORTANT — ON DELETE RESTRICT: biometric_consent is NOT cascade-deleted when the
user account is deleted. The record is retained for 1 year after account deletion
as legal evidence of consent under BIPA. user_deleted_at is set at deletion time.
An APScheduler job purges rows where user_deleted_at < NOW() - 1 year.
Account deletion flow must explicitly set user_deleted_at before deleting the user row.';
```

---

### sync_event_log

Device-side sync debugging. Uploaded to backend on demand or on failure.

```sql
CREATE TABLE sync_event_log (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    event_type   sync_event_type NOT NULL,
    entity_type  sync_entity_type NOT NULL,
    entity_id    UUID NOT NULL,
    detail       TEXT,
    occurred_at  TIMESTAMPTZ NOT NULL,
    uploaded_at  TIMESTAMPTZ
);

COMMENT ON TABLE sync_event_log IS
'Backend copy of the device-side SyncEventLog SwiftData table.
Uploaded automatically on sync failure or on demand via the
Report a Problem flow. Used for diagnosing offline sync issues.
uploaded_at is null on the device until the entry is uploaded.
On the backend, uploaded_at is set to the upload receipt time.
This is not a general audit log — only sync operations are recorded here.';
```

---

### support_report

In-app problem reports submitted by users.

```sql
CREATE TABLE support_report (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    device_model      TEXT NOT NULL,
    ios_version       TEXT NOT NULL,
    app_version       TEXT NOT NULL,
    description       TEXT NOT NULL,
    sync_log_uploaded BOOLEAN NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE support_report IS
'Problem reports submitted via the in-app Report a Problem flow.
Contains the anonymous user_id for correlating with Railway logs and Sentry.
The user_id is the primary diagnostic tool — searchable in all observability systems.
description may contain user-provided text — treat as potentially sensitive.
sync_log_uploaded indicates whether a SyncEventLog batch was uploaded with this report.';
```

---

## Row Level Security Policies

```sql
-- Enable RLS on all user-data tables
ALTER TABLE "user" ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_exercise ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_set ENABLE ROW LEVEL SECURITY;
ALTER TABLE personal_record ENABLE ROW LEVEL SECURITY;
ALTER TABLE job ENABLE ROW LEVEL SECURITY;
ALTER TABLE biometric_consent ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_event_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE support_report ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_request_log ENABLE ROW LEVEL SECURITY;

-- User: read and update own record only
CREATE POLICY user_self ON "user"
    USING (id = auth.uid());

-- Workout: full access to own workouts only
CREATE POLICY workout_owner ON workout
    USING (user_id = auth.uid());

-- Workout exercise: via workout ownership
CREATE POLICY workout_exercise_owner ON workout_exercise
    USING (workout_id IN (SELECT id FROM workout WHERE user_id = auth.uid()));

-- Workout set: via workout exercise ownership
CREATE POLICY workout_set_owner ON workout_set
    USING (workout_exercise_id IN (
        SELECT we.id FROM workout_exercise we
        JOIN workout w ON w.id = we.workout_id
        WHERE w.user_id = auth.uid()
    ));

-- Personal record: own records only
CREATE POLICY pr_owner ON personal_record
    USING (user_id = auth.uid());

-- Job: own jobs, read-only for client (write via service role only)
CREATE POLICY job_owner_read ON job
    FOR SELECT USING (user_id = auth.uid());

-- Biometric consent: read own, NO client writes (backend service role only)
CREATE POLICY biometric_consent_read ON biometric_consent
    FOR SELECT USING (user_id = auth.uid());
-- No INSERT/UPDATE/DELETE policy — service role only

-- Sync event log: read own only
CREATE POLICY sync_log_owner ON sync_event_log
    USING (user_id = auth.uid());

-- Support report: read own only
CREATE POLICY support_report_owner ON support_report
    USING (user_id = auth.uid());

-- AI request log: NO client access — admin/service role only
-- (No policy created — RLS blocks all access except service role)
```

---

## Indexes

```sql
-- Workout history (most common query: user's recent workouts)
CREATE INDEX idx_workout_user_started
    ON workout(user_id, started_at DESC);

-- PR lookup by user and exercise
CREATE INDEX idx_pr_user_exercise
    ON personal_record(user_id, exercise_id);

-- Exercise text search (fuzzy, uses pg_trgm)
CREATE INDEX idx_exercise_name_trgm
    ON exercise USING GIN (name gin_trgm_ops);

-- Exercise exact name lookup (unique constraint provides this)
-- No additional index needed

-- WorkoutExercise ordering within a workout
CREATE INDEX idx_workout_exercise_order
    ON workout_exercise(workout_id, order_index);

-- WorkoutSet ordering within a workout exercise
CREATE INDEX idx_workout_set_order
    ON workout_set(workout_exercise_id, set_number);

-- PR detection query (runs on every set completion)
CREATE INDEX idx_workout_set_pr_detection
    ON workout_set(workout_exercise_id, weight, reps);

-- Job polling by user
CREATE INDEX idx_job_user_status
    ON job(user_id, status, created_at DESC);

-- Job monthly usage count (cost control checks)
CREATE INDEX idx_job_user_type_month
    ON job(user_id, job_type, created_at DESC);

-- Job expiry cleanup (partial index — only in-progress jobs)
CREATE INDEX idx_job_expires
    ON job(expires_at)
    WHERE status IN ('pending', 'processing');

-- AI log expiry cleanup
CREATE INDEX idx_ai_log_expires
    ON ai_request_log(expires_at);

-- Sync log upload status
CREATE INDEX idx_sync_log_upload
    ON sync_event_log(user_id, uploaded_at);
```

---

## V1 Operational Tables

These tables support V1 operational requirements and are included in the V1 migration.

### device_token

Stores APNs device tokens for push notification delivery.

```sql
CREATE TABLE device_token (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    token           TEXT NOT NULL UNIQUE,
    platform        TEXT NOT NULL DEFAULT 'ios',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE device_token IS
'APNs push notification device tokens. One user may have multiple tokens
(multiple devices). Tokens are de-registered on sign-out and when APNs
returns a 410 Gone response (token invalidated by Apple).
CASCADE DELETE ensures tokens are removed when account is deleted.';

ALTER TABLE device_token ENABLE ROW LEVEL SECURITY;
CREATE POLICY device_token_owner ON device_token
    USING (user_id = auth.uid());
```

---

### user_notification_preference

Stores per-user notification schedule and nudge configuration.

```sql
CREATE TABLE user_notification_preference (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                     UUID NOT NULL UNIQUE REFERENCES "user"(id) ON DELETE CASCADE,
    reminder_days               INTEGER[],          -- ISO weekday numbers: 1=Mon, 7=Sun
    reminder_time               TIME,               -- Local time HH:MM
    reminder_timezone           TEXT,               -- IANA timezone e.g. America/Los_Angeles
    nudge_enabled               BOOLEAN NOT NULL DEFAULT true,
    nudge_time                  TIME,               -- Local time — defaults to reminder_time + 2h
    reminder_sent_today         BOOLEAN NOT NULL DEFAULT false,
    nudge_sent_today            BOOLEAN NOT NULL DEFAULT false,
    last_reset_date             DATE,               -- Date reminder_sent_today was last reset
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE user_notification_preference IS
'Per-user workout reminder and nudge notification schedule.
reminder_days uses ISO weekday numbers (1=Monday, 7=Sunday).
reminder_time and nudge_time are stored in local time — always use
reminder_timezone when calculating UTC send time in the backend scheduler.
reminder_sent_today and nudge_sent_today are reset daily by the scheduler
to prevent duplicate sends across service restarts.
UNIQUE on user_id — one preference record per user.';

ALTER TABLE user_notification_preference ENABLE ROW LEVEL SECURITY;
CREATE POLICY notification_pref_owner ON user_notification_preference
    USING (user_id = auth.uid());

CREATE INDEX idx_notification_pref_reminder
    ON user_notification_preference(reminder_time, reminder_days)
    WHERE reminder_days IS NOT NULL;
```

---

### daily_ai_cost

Nightly aggregate of AI token usage. Populated by JOB-007 (daily_ai_cost_summary).

```sql
CREATE TABLE daily_ai_cost (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date                        DATE NOT NULL UNIQUE,
    claude_input_tokens         INTEGER NOT NULL DEFAULT 0,
    claude_output_tokens        INTEGER NOT NULL DEFAULT 0,
    fal_image_calls             INTEGER NOT NULL DEFAULT 0,
    claude_vision_calls         INTEGER NOT NULL DEFAULT 0,
    insight_jobs                INTEGER NOT NULL DEFAULT 0,
    future_self_jobs            INTEGER NOT NULL DEFAULT 0,
    benchmarking_jobs           INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd          NUMERIC(10, 4) NOT NULL DEFAULT 0,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE daily_ai_cost IS
'Daily aggregate of AI API usage and estimated cost. Populated nightly by
the daily_ai_cost_summary APScheduler job (JOB-007). Used for paywall
decision data at V2 and for circuit breaker monitoring.
UNIQUE on date — job uses upsert to handle reruns safely.
No user data — aggregated totals only. No RLS needed (admin read only).';
```

---

### data_subject_request

Log of GDPR/CCPA data subject requests (deletion, access, portability).

```sql
CREATE TABLE data_subject_request (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID,                   -- nullable: user may be deleted by time of review
    request_type        TEXT NOT NULL,          -- 'deletion' | 'access' | 'portability'
    status              TEXT NOT NULL DEFAULT 'pending',  -- pending | in_progress | complete
    submitted_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged_at     TIMESTAMPTZ,            -- within 72 hours of receipt
    completed_at        TIMESTAMPTZ,            -- within 30 days
    notes               TEXT,                   -- internal notes only, never shown to user
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE data_subject_request IS
'Log of all GDPR and CCPA data subject requests received. Retained for 3 years
as compliance evidence. user_id is nullable because the account may be deleted
during the fulfillment window. request_type covers deletion (right to erasure),
access (right of access), and portability (right to data portability — V2).
acknowledged_at must be within 72 hours. completed_at must be within 30 days.
No RLS — admin/service role access only.';
```

---

## V2 Tables (Not in V1 Migration)

These tables are documented for reference. They are not created in V1 migrations.

- `workout_plan` — structured multi-week programs
- `workout_plan_day` — days within a plan
- `workout_plan_exercise` — prescribed exercises per plan day
- `body_metrics` — weight, measurements, body fat %
- `steps_entry` — daily steps and calorie aggregates

