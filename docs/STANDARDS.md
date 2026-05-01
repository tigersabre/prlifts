# PRLifts — Engineering Standards

**Version:** 1.0
**Status:** Living document — changes require review from the relevant domain lead
**Last updated:** April 2026
**Audience:** All developers, including junior developers and Claude Code

> These standards apply to every line of code in every layer of the system.
> They exist to make the codebase readable, maintainable, and recoverable
> by anyone — including someone who didn't build it and is debugging it at 2am.
>
> If you are unsure whether something is right, check this document first.
> If this document doesn't answer your question, ask before assuming.

---

## Table of Contents

1. [Software Craftsmanship](#1-software-craftsmanship)
2. [Security Coding Standards](#2-security-coding-standards)
3. [Testing Standards](#3-testing-standards)
4. [DevOps and Operational Standards](#4-devops-and-operational-standards)
5. [Data Standards](#5-data-standards)
6. [iOS Platform Standards](#6-ios-platform-standards)
7. [Backend Platform Standards](#7-backend-platform-standards)
8. [AI/ML Standards](#8-aiml-standards)
9. [UX and Copy Standards](#9-ux-and-copy-standards)
10. [Privacy and Compliance Standards](#10-privacy-and-compliance-standards)
11. [Definition of Done](#11-definition-of-done)
12. [Tooling Enforcement Summary](#12-tooling-enforcement-summary)

---

## 1. Software Craftsmanship

> Owned by: Staff/Principal Engineer
> Applies to: All code in all layers

### 1.1 Why This Exists

Code is read far more than it is written. Junior developers, future collaborators, and
Claude Code all need to understand what code does, why it does it, and how to change it
safely. These standards make that possible without requiring a conversation with whoever
wrote it.

### 1.2 Naming

**The rule:** Names should tell you what something does without needing a comment to
explain them. If you need a comment to explain a name, the name is wrong.

**Swift examples:**

```swift
// BAD — vague, requires mental translation
func process(_ data: WorkoutData) -> Bool
let wktExId: UUID

// GOOD — reads like a sentence
func detectsNewPersonalRecord(in set: WorkoutSet) -> Bool
let workoutExerciseID: UUID
```

**Python examples:**

```python
# BAD — what does this do?
def handle_ai(workout, user):

# GOOD — unambiguous
def generate_workout_insight(workout: Workout, user: User) -> str:
```

**Rules:**
- No abbreviations except these approved domain terms: `id`, `url`, `api`, `db`, `rpe`, `pr`
- Booleans are always a question: `isCompleted`, `hasActiveConsent`, `shouldSyncNow`
- Collections are always plural: `workouts`, `exercises`, `sets`
- Functions returning a value are named for what they return: `personalRecord()` not `getPersonalRecord()`
- Functions performing an action are named for the action: `syncPendingWorkouts()` not `workoutSync()`

### 1.3 Comments

**The rule:** Comment the *why*, never the *what*. The code explains what it does.
Only you know why you made a specific choice.

```swift
// BAD — restates what the code already says
// Check if the set is completed
guard set.isCompleted else { return nil }

// GOOD — explains a non-obvious decision
// Only detect PRs on completed sets — partial sets during an active
// workout would create false PRs that pollute the user's history
guard set.isCompleted else { return nil }
```

```python
# BAD — obvious
# Return 202 status code
return JSONResponse(status_code=202, content={"job_id": str(job.id)})

# GOOD — explains the decision
# Return 202 Accepted rather than 200 OK — the work is not done yet.
# The client polls GET /v1/jobs/{id} for the result.
return JSONResponse(status_code=202, content={"job_id": str(job.id)})
```

**Rules:**
- Every module (Swift file, Python module) has a one-paragraph header explaining its
  purpose and its place in the architecture
- Every public function has a docstring explaining its purpose, parameters, and return value
- Complex algorithms get a plain English explanation before the code, not inline
- `TODO:` and `FIXME:` must include a GitHub issue number: `// TODO: #123 — add retry logic`
- Never commit commented-out code — delete it, git has history

### 1.4 Function and Method Size

**The rule:** If a function does not fit on one screen without scrolling, it is doing
too much.

- Maximum 40 lines of implementation logic per function (docstrings excluded)
- Maximum 3 levels of nesting
- Maximum 4 parameters — if you need more, introduce a struct or dataclass
- One responsibility per function — if the name contains "and", split it

```swift
// BAD — too many responsibilities, name says "and"
func processWorkoutAndDetectPRAndSendNotification(workout: Workout) { }

// GOOD — each function has one job
func saveCompletedWorkout(_ workout: Workout) throws { }
func detectPersonalRecords(in workout: Workout) -> [PersonalRecord] { }
func scheduleNotification(for record: PersonalRecord) { }
```

Test functions are exempt from the 40-line limit when the Arrange/Act/Assert
structure legitimately requires more space.

### 1.5 Error Handling

**The rule:** Errors are first-class information. They must be named, structured, and
handled explicitly. Never swallow an error silently.

**Swift:**

```swift
// Define domain errors as enums — they are self-documenting
enum PRLiftsError: Error {
    case syncFailed(reason: String, entityID: UUID)
    case aiProviderUnavailable(provider: String, statusCode: Int)
    case biometricConsentRequired
    case jobExpired(jobID: UUID)
}

// BAD — swallowed error, you will never know why it failed
try? saveWorkout(workout)

// GOOD — explicit handling with a meaningful response
do {
    try saveWorkout(workout)
} catch PRLiftsError.syncFailed(let reason, let id) {
    logger.error("Sync failed for entity \(id): \(reason)")
    syncEventLog.record(.syncFailure, entityID: id, detail: reason)
}
```

**Python:**

```python
# Define domain exceptions with useful context
class PRLiftsError(Exception):
    """Base exception for all PRLifts domain errors."""

class AIProviderError(PRLiftsError):
    """Raised when an AI provider call fails."""
    def __init__(self, provider: str, status_code: int, message: str):
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"{provider} returned {status_code}: {message}")

# BAD — bare except swallows everything, including bugs
try:
    result = await generate_insight(workout)
except:
    pass

# GOOD — specific, logged, graceful fallback
try:
    result = await generate_insight(workout)
except AIProviderError as e:
    logger.error(
        "AI insight generation failed",
        provider=e.provider,
        status_code=e.status_code,
        job_id=str(job.id)
    )
    return JobResult(status="failed", message="Insight unavailable — try again later")
```

### 1.6 Code Review Standards

**What reviewers must check:**
- Names follow conventions — flag anything that needs a comment to explain itself
- No function over 40 lines of implementation logic
- Errors are handled explicitly — no bare `try?` or bare `except`
- Tests cover the new behaviour, not just the happy path
- No secrets, PII, or sensitive data in code, comments, or test fixtures
- Definition of Done checklist is complete

**What reviewers should NOT block on:**
- Personal style preferences not covered by a defined standard
- Formatting that the linter would catch — let the linter do it
- Suggestions vs. requirements — label non-blocking feedback as `[suggestion]`

**Review turnaround:**
- Under 200 lines: same working day
- Over 200 lines: next working day

### 1.7 Refactoring Policy

- Boy Scout Rule: leave code cleaner than you found it — a small improvement in a file
  you are already changing is always welcome
- Technical debt is tracked as GitHub Issues with label `debt` and milestone for the
  intended fix version
- No refactoring PRs that also add features — refactor first, then add the feature in
  a separate PR. This keeps diffs readable.

---

## 2. Security Coding Standards

> Owned by: Security Standards Lead / Security Architect
> Applies to: All code in all layers

### 2.1 Why This Exists

Security vulnerabilities are almost always introduced at the code level, not the
architecture level. These standards make secure coding the default so developers do not
have to remember to apply security — it is built into the patterns.

### 2.2 Hard Rules — Never in Code

These are absolute. CI will check for them. A PR containing any of these cannot merge.

```python
# NEVER — hardcoded secret
CLAUDE_API_KEY = "sk-ant-..."

# NEVER — SQL string concatenation (SQL injection risk)
query = f"SELECT * FROM workout WHERE user_id = '{user_id}'"

# NEVER — PII in logs
logger.info(f"User {user.email} logged in")

# NEVER — user-controlled input in file paths
file_path = f"/uploads/{request.filename}"
```

```swift
// NEVER — auth token in UserDefaults
UserDefaults.standard.set(authToken, forKey: "auth_token")

// NEVER — sensitive data in logs
print("User photo: \(photoData)")
```

### 2.3 Input Validation

Every API endpoint validates all inputs before processing. Validation is the first
thing that happens — never an afterthought added later.

```python
# Pydantic validates before the handler runs
class LogWorkoutSetRequest(BaseModel):
    workout_exercise_id: UUID
    set_number: int = Field(ge=1, le=100)       # 1 to 100 sets maximum
    weight: Optional[float] = Field(None, ge=0, le=2000)  # 0 to 2000 kg/lbs
    reps: Optional[int] = Field(None, ge=0, le=1000)
    rpe: Optional[int] = Field(None, ge=1, le=10)
```

**Rules:**
- Every field has explicit bounds — no unbounded string or number inputs from users
- File uploads validate type, size, and magic bytes — not just filename extension
- A 413 response for oversized inputs, not a silent truncation

### 2.4 Unified Log Level Standard

| Level | What it means | Retention | Alerting |
|---|---|---|---|
| DEBUG | Detailed flow — development only, disabled in production | Not retained | None |
| INFO | Normal operations, state transitions, completions | 7 days in Railway | None |
| WARNING | Unexpected but handled: rate limit hit, quality gate failed, retry triggered | 7 days | None |
| ERROR | Unexpected, not fully handled: provider unavailable, job expired | Sentry capture | Email |
| CRITICAL | System-level failure: database unreachable, scheduler stopped | Sentry capture | SMS |

All logs include `correlation_id` — a UUID generated per request, passed through all
downstream calls, present on every log line for that request. This lets you trace a
single user issue through the entire system by searching one ID.

```python
logger.info(
    "Workout insight generated",
    correlation_id=request.state.correlation_id,
    job_id=str(job.id),
    user_id=str(user.id),   # anonymous UUID — not email or name
    duration_ms=elapsed
)
```

### 2.5 Dependency Security

Before adding any new dependency:
1. Check last commit date — reject if unmaintained for over 12 months
2. Run `pip audit` (Python) or check swift package audit — reject known vulnerabilities
3. Check community size — avoid obscure packages with no community support
4. Document the reason in the PR description: "Added X because Y and we evaluated Z"

`pip audit` runs in CI on every push.

### 2.6 Security Review Checklist (Per Feature)

Before any feature touching user data is marked Done:

- [ ] All inputs validated with explicit bounds
- [ ] No PII in any log statement
- [ ] No secrets in code, comments, or test fixtures
- [ ] RLS policies verified for any new Supabase table
- [ ] New endpoints have rate limiting applied
- [ ] Error messages shown to users contain no internal details
- [ ] Any new third-party integration has a DPA reviewed before shipping

---

## 3. Testing Standards

> Owned by: QA Standards Lead / QA Architect
> Applies to: All test code in all layers

### 3.1 Why This Exists

Tests are documentation that runs. A well-written test tells the next developer exactly
what a piece of code is supposed to do and proves it still does it. Poorly written tests
are worse than no tests — they give false confidence and break for the wrong reasons.

### 3.2 Test Naming

Test names are sentences. Reading a test name should tell you exactly what is being
verified, without opening the test.

**Format:** `test_[unit under test]_[scenario]_[expected outcome]`

```swift
// BAD — tells you nothing
func testPRDetection() { }

// GOOD — tells you the scenario and what should happen
func test_detectsPersonalRecord_whenNewWeightExceedsPreviousBest() { }
func test_doesNotDetectPersonalRecord_whenWeightEqualsButRPEIsHigher() { }
func test_createsSeperateRecord_forWeightedAndBodyweightVariants() { }
```

```python
# BAD
def test_ai_service():

# GOOD
def test_generate_insight_returns_fallback_when_provider_unavailable():
def test_quality_gate_rejects_image_when_score_below_threshold():
def test_job_expires_after_five_minutes_with_no_completion():
```

**Language convention:** Python tests use `snake_case`. Swift tests use `camelCase`.
Both follow the same sentence structure.

### 3.3 Test Structure — Arrange, Act, Assert

Every test follows AAA. Each section is labeled with a comment. No exceptions.

```swift
func test_detectsPersonalRecord_whenNewWeightExceedsPreviousBest() {
    // Arrange
    let previousBest = WorkoutSet.stub(weight: 100, weightUnit: .kg, reps: 5)
    let newSet = WorkoutSet.stub(weight: 105, weightUnit: .kg, reps: 5)
    let sut = PersonalRecordDetector(previousBest: previousBest)

    // Act
    let result = sut.detect(newSet: newSet)

    // Assert
    XCTAssertNotNil(result)
    XCTAssertEqual(result?.value, 105)
}
```

```python
def test_job_expires_after_five_minutes_with_no_completion():
    # Arrange
    job = Job.create(job_type="future_self", user_id=TEST_USER_ID)
    job.expires_at = datetime.utcnow() - timedelta(minutes=6)

    # Act
    cleanup_expired_jobs()

    # Assert
    refreshed = Job.get(job.id)
    assert refreshed.status == "expired"
    assert refreshed.error_message is not None
```

### 3.4 Test Data Management

Use stub factories — never raw constructors. Raw constructors break every test when a
new required field is added to the model.

```swift
// BAD — breaks when WorkoutSet gains a new required field
let set = WorkoutSet(
    id: UUID(),
    workoutExerciseID: UUID(),
    setNumber: 1,
    // ... 14 more required fields ...
)

// GOOD — only set what your test cares about
let set = WorkoutSet.stub(weight: 100, weightUnit: .kg)
```

**Rules:**
- Every model has a `.stub()` factory with sensible defaults
- Stubs live in a `TestSupport` target — never in production code
- No real user data in test fixtures — ever
- No hardcoded UUIDs in tests — use `UUID()` or named constants

### 3.5 Defect Classification

Every bug filed in GitHub Issues gets a severity label:

| Label | Definition | Target fix |
|---|---|---|
| `sev-1-critical` | Data loss, security breach, app unusable for all users | Same day |
| `sev-2-high` | Core feature broken, no workaround | Next working day |
| `sev-3-medium` | Feature degraded, workaround exists | Next sprint |
| `sev-4-low` | Minor, cosmetic, edge case | Backlog |

Every `sev-1` and `sev-2` gets a post-mortem note in the GitHub issue after fix:
what broke, why, how it was missed, what prevents recurrence.

### 3.6 Acceptance Criteria Template

Every GitHub Issue must have acceptance criteria written in Given/When/Then format
before implementation begins. This is the test specification.

```
## Acceptance Criteria

Given [the initial state]
When [the action occurs]
Then [the expected outcome]
And [additional expected outcomes]

Example:

Given a user has completed a workout set with weight 105kg
When PR detection runs
Then a PersonalRecord is created with value 105
And the previous record value is stored on the new record
And WorkoutSet.set_type is updated to .pr

Given a user has completed a workout set equal to their previous best
When PR detection runs
Then no PersonalRecord is created
```

---

## 4. DevOps and Operational Standards

> Owned by: Platform Engineering Lead / SRE Lead
> Applies to: Infrastructure, deployment, incident response

### 4.1 Why This Exists

When things break — and they will — the speed of recovery depends entirely on how
well the system was built to be operated. These standards exist to make the system
diagnosable and recoverable by anyone, including someone who has never seen it before.

### 4.2 Incident Classification and Response

| Level | Definition | Response time | Post-mortem |
|---|---|---|---|
| P1 | All users affected, core feature down | Immediate | Required within 48 hours |
| P2 | Significant subset affected | Within 1 hour | Required within 48 hours |
| P3 | Single feature degraded, workaround exists | Within 4 hours | Optional |
| P4 | Minor issue, no user impact | Next working day | None |

**MTTR targets:** P1 < 1 hour. P2 < 4 hours. P3 < 8 hours.

Post-mortems are learning documents, not blame documents. They answer: what broke,
why, how it was missed, and what prevents recurrence. Template: `docs/POSTMORTEM_TEMPLATE.md`.

### 4.3 Deployment Standards

Every deployment:
1. Deployed to staging first — verified manually for the specific change
2. Promoted to production only after staging verification passes
3. Monitored for 15 minutes after production deploy — error rate and latency
4. Rolled back immediately if error rate increases by more than 1%

Feature flags for risky changes: any backend change affecting AI operations,
biometric data, or auth is deployed behind a PostHog feature flag in production.
The flag is enabled only after monitoring confirms staging is healthy.

### 4.4 Environment Parity

Staging mirrors production at all times:
- Same Railway service configuration
- Same Supabase schema and RLS policies
- Same Upstash Redis configuration
- Same APScheduler configuration
- Different data only — staging uses synthetic data, never production data

Any infrastructure change is applied to staging first, verified, then production.
All infrastructure changes are documented in `docs/INFRASTRUCTURE_CHANGES.md` before
being applied — until infrastructure-as-code is introduced in V2.

### 4.5 On-Call Standards

- Sentry alerts go to email — checked daily
- P1 Sentry alerts go to SMS — configured before public launch
- The runbook (`docs/RUNBOOK.md`) is the first thing opened for any incident
- Every incident gets a one-line note in `docs/INCIDENT_LOG.md`:
  date, what happened, how it was resolved

### 4.6 Correlation ID Standard

Every HTTP request gets a `correlation_id` UUID assigned by middleware. This ID is:
- Included in every log line for that request
- Returned in the response header `X-Correlation-ID`
- Passed to all downstream service calls
- Used to find all logs related to a single user-reported issue

When a user reports a problem, the correlation ID from their request is the search key.

---

## 5. Data Standards

> Owned by: Data Governance Lead
> Applies to: All database schemas, migrations, and queries

### 5.1 Why This Exists

Database schemas outlive the code that creates them. A poorly named column or a missing
constraint discovered after launch costs 10x more to fix than getting it right the first
time. These standards ensure the database is as readable as the application code.

### 5.2 Naming Conventions

**Tables:** `snake_case`, singular noun.

```sql
-- GOOD
workout
workout_set
personal_record
biometric_consent

-- BAD
Workouts
workoutSets
PRs
```

**Columns:** `snake_case`. Booleans use `is_` or `has_` prefix.

```sql
-- GOOD
is_completed, has_active_plan, started_at, expires_at

-- BAD
completed, activePlan, startedAt
```

**Foreign keys:** `{referenced_table}_id`

```sql
-- GOOD
user_id, workout_exercise_id, prompt_template_id

-- BAD
userId, exercise_fk, promptId
```

**Timestamps:** Always `created_at` and `updated_at`. Always UTC. Never local time.

**Enum values:** `snake_case`

```sql
-- GOOD
'in_progress', 'partial_completion', 'completed'

-- BAD
'InProgress', 'partialCompletion', 'Completed'
```

### 5.3 Migration Standards

Every schema change is a migration file. No manual database changes. Ever.

**File naming:** `{timestamp}_{description}.sql`
```
20260425_001_add_goal_to_user.sql
20260425_002_create_biometric_consent_table.sql
```

**Migration rules:**
- Every migration includes both `up` and `down` scripts
- Migrations never delete data without an explicit backup step first
- New columns are always nullable first, backfilled, then made non-null in a separate migration
- Every migration is tested in staging before production
- Use a transaction where PostgreSQL supports it for the operation

```sql
-- GOOD — safe, reversible column addition
-- up
ALTER TABLE "user" ADD COLUMN goal TEXT;

-- down
ALTER TABLE "user" DROP COLUMN IF EXISTS goal;
```

### 5.4 Data Dictionary

Every table and every non-obvious column has a `COMMENT` in PostgreSQL. A junior
developer should understand any table's purpose from its comment without reading the
architecture document.

```sql
COMMENT ON TABLE biometric_consent IS
'Legal audit record of user consent to biometric data processing.
Backend-write-only — no direct client writes permitted via RLS.
Required before future_self_enabled flag activates per user.';

COMMENT ON COLUMN biometric_consent.policy_text_hash IS
'SHA-256 hash of the exact consent policy text shown to the user.
Tamper-evident record of what the user agreed to.';
```

**Mandatory rule:** Every table in every migration must have a `COMMENT ON TABLE` before
the migration is merged. Migrations without table comments are a blocking PR issue. Column
comments are required when the purpose is not immediately obvious from the name alone.

### 5.5 Query Standards

```python
# BAD — SQL injection risk, unreadable
result = db.execute(f"SELECT * FROM workout WHERE user_id = '{user_id}'")

# GOOD — parameterized, readable, safe
result = db.execute(
    select(Workout)
    .where(Workout.user_id == user_id)
    .order_by(Workout.started_at.desc())
    .limit(20)
)
```

**Rules:**
- All queries are parameterized — never string-formatted
- All queries returning multiple rows have an explicit `LIMIT`
- Hot path queries (PR detection, workout history) are verified with `EXPLAIN ANALYZE`
  before going to production
- N+1 queries are a blocking PR issue — use joins or `selectinload`

### 5.6 Schema Consistency

SCHEMA.md is the single source of truth for both PostgreSQL (Alembic migrations) and SwiftData models (PRLiftsCore).

**Column annotations:**
Every column in SCHEMA.md is annotated as either:
- `[iOS]` — maps to a SwiftData property in PRLiftsCore
- `[BE]` — backend-only, no SwiftData counterpart required or permitted

**The pairing rule:**
Any story that changes an `[iOS]` annotated column must update ALL THREE in the same PR:
- The Alembic migration
- The SwiftData model in PRLiftsCore
- SCHEMA.md

No partial updates permitted. A migration that changes an `[iOS]` column without a corresponding SwiftData update is a blocking PR issue.

**BiometricConsent is permanently `[BE]`:**
Creating a SwiftData model for BiometricConsent is a blocking security and legal violation — not a style preference. BiometricConsent records exist server-side only, protected by backend-write-only RLS. A client-side copy would create a path for consent record manipulation.

**Naming convention:**
PostgreSQL `snake_case` maps deterministically to SwiftData `camelCase`:
- `workout_exercise_id` → `workoutExerciseID`
- `is_completed` → `isCompleted`
- `created_at` → `createdAt`
- `rpe` → `rpe` (domain abbreviation — unchanged)
- `id` → `id` (unchanged)

Document any non-obvious mapping in a comment on the SwiftData property.

**CI enforcement:**
A schema consistency CI test runs in GitHub Actions as part of backend-ci.
It parses SCHEMA.md annotations and validates a `SchemaMapping.swift` committed to PRLiftsCore. The 5 test cases it must verify:
1. SwiftData model exists for every `[iOS]` annotated column
2. SwiftData property name follows camelCase convention
3. SwiftData property type is compatible with PostgreSQL column type
4. No SwiftData property exists for `[BE]` annotated columns
5. Every column in SCHEMA.md has an annotation — no unannotated columns

**Backend-only column rule:**
Backend operational columns (indexes, audit fields, cost tracking) that have no user-facing data purpose are annotated `[BE]` and require no SwiftData counterpart. Adding them to SwiftData without a documented reason is a style violation.

---

## 6. iOS Platform Standards

> Owned by: iOS Platform Lead
> Applies to: ios-app/ and core-library/

### 6.1 Why This Exists

SwiftUI and SwiftData have specific patterns that work well and anti-patterns that look
fine but cause subtle bugs. These standards encode that knowledge so junior developers
do not have to discover the hard way.

### 6.2 File Organization

Every Swift file follows this structure in this order:

```swift
// 1. Module header comment — purpose and architecture placement
// WorkoutLogger.swift
// PRLifts Core Library
//
// Logs a completed WorkoutSet to the local SwiftData store
// and queues it for sync to the backend. Primary write path
// for all workout data.

import Foundation
import SwiftData

// 2. Protocols (if this file defines them)
protocol WorkoutLogging {
    func log(_ set: WorkoutSet) throws
}

// 3. Main type
final class WorkoutLogger: WorkoutLogging {

    // 4. Properties — constants first, variables second, private last
    let store: ModelContext
    private let syncQueue: SyncQueue

    // 5. Initializer
    init(store: ModelContext, syncQueue: SyncQueue) { ... }

    // 6. Public interface
    func log(_ set: WorkoutSet) throws { ... }

    // 7. Private implementation
    private func validateSet(_ set: WorkoutSet) throws { ... }
}

// 8. Extensions — one per conformance
extension WorkoutLogger: Equatable { ... }
```

### 6.3 SwiftUI — Views Are Thin

Views contain no business logic. Formatting, calculation, and decisions belong in
ViewModels or the Core Library.

```swift
// BAD — business logic and formatting in the View
struct WorkoutSetRow: View {
    var body: some View {
        Text("\(set.weight) kg")  // formatting in View
        if set.weight > previousBest { ... }  // business logic in View
    }
}

// GOOD — View only displays what the ViewModel provides
struct WorkoutSetRow: View {
    let viewModel: WorkoutSetRowViewModel

    var body: some View {
        Text(viewModel.formattedWeight)
        if viewModel.isPersonalRecord { ... }
    }
}
```

**Rules:**
- `@State` only for transient UI state (is a sheet showing, is a button tapped)
- `@Environment` only for system values (colorScheme, dismiss)
- ViewModels are plain Swift — no SwiftUI imports
- Never force-unwrap optionals in production code

### 6.4 SwiftData — Writes on Background Context

```swift
// BAD — blocks the main thread
@MainActor
func saveWorkout(_ workout: Workout) {
    modelContext.insert(workout)
    try? modelContext.save()
}

// GOOD — background context, explicit error handling
func saveWorkout(_ workout: Workout) async throws {
    let container = modelContext.container
    try await container.performBackgroundTask { context in
        context.insert(workout)
        try context.save()
    }
}
```

**Rules:**
- Model mutations on background context, never main context
- `try?` is never used with SwiftData — failures must be caught and logged
- All timestamps stored as UTC — `DateFormatter` with user timezone at display layer only

### 6.5 Accessibility

Every interactive element requires accessibility annotations.

```swift
Button(action: logSet) {
    Image(systemName: "plus.circle")
}
.accessibilityLabel("Log set")
.accessibilityHint("Adds this set to your workout")
```

**Rules:**
- Every `Image` has `.accessibilityLabel` or `.accessibilityHidden(true)` if decorative
- All text supports Dynamic Type — never hardcode font sizes
- Minimum touch target 44×44pt on all interactive elements
- VoiceOver reading order is logical — use `.accessibilitySortPriority` where needed
- Accessibility tests run in CI via `XCTOSSignpostMetric` accessibility audit
- UI tests must be run against iPhone SE (3rd generation) simulator before opening any iOS PR. The SE's 320pt width is the minimum supported screen size. Touch targets must meet 44×44pt minimum on all screen sizes.
- Never use `guard element.waitForExistence() else { return }` in UI tests — use `XCTAssertTrue(element.waitForExistence(timeout:))` so failures are loud and immediate.

### 6.6 NWPathMonitor Thread Safety

`NWPathMonitor` callbacks arrive on a background thread. Any code that follows a
connectivity change notification and touches SwiftData or updates UI must dispatch
to the correct queue first.

```swift
// GOOD — dispatches to main before touching UI or SwiftData
monitor.pathUpdateHandler = { path in
    DispatchQueue.main.async {
        if path.status == .satisfied {
            self.syncPendingWorkouts()
        }
    }
}
```

---

## 7. Backend Platform Standards

> Owned by: Backend Platform Lead
> Applies to: backend/

### 7.1 Why This Exists

FastAPI and Python have enough flexibility to write the same feature ten different ways.
These standards pick one right way for each pattern so the codebase is consistent and
any developer always knows what to look for.

### 7.2 FastAPI Route Structure

```python
from fastapi import APIRouter, Depends, status
from app.auth import get_current_user
from app.models import User
from app.schemas import LogWorkoutSetRequest, WorkoutSetResponse

router = APIRouter(prefix="/v1/workout-sets", tags=["workout-sets"])

@router.post(
    "/",
    response_model=WorkoutSetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a completed workout set",
    description="""
    Records a single completed set within a workout exercise.
    Triggers PR detection after successful save.
    Returns the saved set with any detected PR information.
    """
)
async def log_workout_set(
    request: LogWorkoutSetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkoutSetResponse:
    return await workout_service.log_set(request, user_id=current_user.id, db=db)
```

**Rules:**
- Every route has `summary` and `description` — these appear in the OpenAPI spec
- Route functions are thin: validate input, call a service, return a response
- Business logic lives in `services/` — never in route handlers
- All routes use typed Pydantic response models — never return raw dicts

### 7.3 Service Layer

```python
class WorkoutService:
    """
    Handles all business logic for workout operations.

    This is the only place that coordinates between the database,
    PR detection, and sync queue. Route handlers call this service —
    they do not touch the database directly.
    """

    def __init__(self, db: AsyncSession, pr_detector: PRDetector):
        # Dependencies injected — never instantiated inside the service
        self.db = db
        self.pr_detector = pr_detector

    async def log_set(
        self,
        set_data: LogWorkoutSetRequest,
        user_id: UUID
    ) -> WorkoutSet:
        """
        Saves a completed workout set and triggers PR detection.

        Args:
            set_data: Validated set data from the route handler
            user_id: The authenticated user's ID

        Returns:
            The saved WorkoutSet with PR status populated

        Raises:
            WorkoutExerciseNotFoundError: If the workout exercise does not exist
            UnauthorizedError: If the workout does not belong to this user
        """
```

### 7.4 Type Annotations

Every function signature is fully type-annotated. mypy runs in CI and blocks on errors.

```python
# BAD
def calculate_pr(new_set, previous_sets):
    pass

# GOOD
def calculate_pr(
    new_set: WorkoutSet,
    previous_sets: list[WorkoutSet]
) -> PersonalRecord | None:
    """Returns a PersonalRecord if new_set beats all previous_sets, else None."""
```

### 7.5 API Error Response Standard

All error responses use a consistent structure:

```python
class ErrorResponse(BaseModel):
    error_code: str    # machine-readable: "rate_limit_exceeded"
    message: str       # human-readable: "Too many requests. Try again in 60 seconds."
    request_id: str    # correlation ID for support queries
```

**Error code convention:** `snake_case`, domain-prefixed:
```
workout_not_found
ai_provider_unavailable
biometric_consent_required
rate_limit_exceeded
job_expired
quality_gate_failed
```

### 7.6 APScheduler Standard

The job cleanup task runs via APScheduler AsyncIOScheduler. It must be started inside
FastAPI's `lifespan` context manager — not the deprecated `@app.on_event("startup")`.

```python
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start scheduler on app startup
    scheduler.add_job(cleanup_expired_jobs, "interval", seconds=60)
    scheduler.start()
    yield
    # Stop scheduler on app shutdown
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
```

---

## 8. AI/ML Standards

> Owned by: ML Platform Lead
> Applies to: All AI-related code and prompt templates

### 8.1 Why This Exists

AI code has unique failure modes that standard testing does not catch. A prompt that
works 95% of the time looks fine in testing and produces harmful output for 5% of
users. These standards make AI behaviour explicit, testable, and auditable.

### 8.2 Prompt Engineering

Prompts are code. They are version-controlled in the PromptTemplate table, reviewed
before activation, and never hardcoded.

**Every prompt follows this structure:**

```
[ROLE]
You are a fitness coach AI for PRLifts, a workout tracking app.

[CONTEXT]
{structured_user_context}  ← structured data, never raw user input

[TASK]
{specific task description}

[CONSTRAINTS]
- Maximum {n} sentences
- Never give medical advice
- Frame all feedback as encouragement, not criticism
- If data is insufficient, say so honestly

[OUTPUT FORMAT]
{exact format specification}
```

**Rules:**
- User-provided text (workout names, notes) is never interpolated directly into prompts —
  it is summarised by a safe preprocessing step first
- Every prompt specifies a maximum response length
- Every prompt includes explicit constraints on what the model must not say
- Changes to any prompt template require a content review before activation
- Changes to `config/ai_forbidden_phrases.txt` require the same content review

### 8.3 Prompt Evaluation

Before a new prompt version is activated:

1. Run against 20 defined test cases in `tests/prompt_evaluation/`
2. Score on: accuracy, tone, length compliance, constraint adherence
3. Must score equal or better than the current active prompt on all dimensions
4. Body image prompt evaluation is a **blocking CI gate**
5. All other prompt evaluations are informational (non-blocking) in CI
6. Activation requires explicit approval — not automatic

**Initial test cases:** The first 20 prompt evaluation test cases must be written before
any prompt template is activated in any environment. They are authored by the developer
activating the first prompt and reviewed before merge. Once written, they become a
permanent regression suite that new prompt versions must pass.

### 8.4 AI Response Validation

AI responses are validated before being returned to users:

```python
def validate_insight_response(response: str) -> InsightValidationResult:
    """
    Validates an AI-generated workout insight before returning to the user.

    Checks length, forbidden phrases, and PII leakage.
    Returns a result — never raises. Caller decides what to do on failure.
    """
```

**Forbidden phrases** (`config/ai_forbidden_phrases.txt`) — checked on every response:
- Medical diagnostic language: "you have", "you may be suffering from"
- Extreme body language: "lose weight", "burn fat", "slim down", "thinner"
- Absolute claims: "you will", "guaranteed", "always"

### 8.5 Quality Gate Behaviour

- Generate 2 Fal.ai variations per image generation request
- Score each with a Claude vision call on a 1–10 face similarity scale
- Present the highest-scoring variation if score >= 6
- If both variations score below 6: show fallback message, do not show image
- If the Claude vision scoring call itself fails: **fail-closed** — show fallback message,
  do not show unscored image, log `quality_score: null` in AIRequestLog
- A high null-score rate triggers a Sentry alert for investigation

This is a product decision: showing a poor future self image is a worse experience
than a thoughtful fallback message.

### 8.6 AI Cost Tracking

Every AI call logs token usage and cost signals:

```python
logger.info(
    "Claude API call complete",
    feature=feature_name,
    prompt_template_id=str(prompt.id),
    prompt_template_version=prompt.version,
    input_tokens=response.usage.input_tokens,
    output_tokens=response.usage.output_tokens,
    quality_score=quality_score,  # None if not applicable
    duration_ms=elapsed,
    user_id=str(user_id)
)
```

A daily cost summary runs at midnight and is stored in `daily_ai_cost` table.

---

## 9. UX and Copy Standards

> Owned by: Design Systems Lead
> Applies to: All user-facing text and interface states

### 9.1 Why This Exists

Inconsistent UX and copy erodes trust. When buttons say different things on different
screens, or error messages are written in different tones, users feel the app was not
built with care. These standards make the experience feel like one consistent product.

### 9.2 Voice and Tone

**Voice:** Direct, warm, encouraging. Never clinical. Never condescending.

```
BAD — clinical
"Biometric data processing consent required"

GOOD — warm and direct
"Before we create your future self image, we need your permission to process your photo."

BAD — condescending
"You haven't logged a workout yet! Why not start now? 💪"

GOOD — respectful
"Ready when you are. Tap to log your first workout."

BAD — technical error
"Error 429: Rate limit exceeded"

GOOD — human
"You've hit your daily insight limit. Come back tomorrow for your next one."
```

### 9.3 Copy Rules

- Sentence case for all UI text — not Title Case
- No exclamation marks except in defined celebration moments (see below)
- No passive voice: "Your workout was saved" becomes "Workout saved"
- Emoji only in defined celebration moments — never in error, empty, or loading states

**Defined celebration moments where one emoji and one exclamation mark are permitted:**
- PR achieved notification
- First workout completed
- First future self image revealed

No other exceptions without a documented decision.

### 9.4 Empty States

Every screen that can be empty has a defined empty state. Blank screens are never
acceptable.

Every empty state has exactly three elements:
1. **Illustration or icon** — relevant to the content, not a generic stock image
2. **Heading** — what is empty, in plain language
3. **Action** — the one thing the user should do next

```
Example — workout history:
[Barbell icon]
No workouts yet
[Button: Log your first workout]
```

### 9.5 Loading States

- Content that will fill a known layout uses a skeleton screen, not a spinner
- AI operations use progressive messaging (defined in ARCHITECTURE.md)
- Maximum wait messaging shows a time estimate from the third polling attempt onward
- Loading states never display technical information

### 9.6 Error State Hierarchy

| Error type | What to show | Never show |
|---|---|---|
| Network unavailable | "You're offline. Changes will sync when you reconnect." | Technical error |
| AI unavailable | Feature-specific fallback message | "503 Service Unavailable" |
| Rate limit | "You've reached your daily limit. Try again tomorrow." | Error code |
| Form validation | Inline field-level message | Toast for form errors |
| Quality gate failed | "Your vision is being crafted — check back soon" | Technical failure |
| Unknown | "Something went wrong. We've been notified." | Stack trace or error code |

---

## 10. Privacy and Compliance Standards

> Owned by: Privacy Counsel / Data Protection Officer
> Applies to: All data collection, storage, and processing

### 10.1 Why This Exists

Privacy violations happen in code, not in policies. These standards make compliant
data handling the default pattern so developers do not have to remember to apply it.

### 10.2 Data Minimisation

Collect only what is needed for a specific, documented purpose.

Before adding any new data collection point, answer these questions in the PR description:
1. What specific feature requires this data?
2. How long will it be retained?
3. Is it disclosed in the Privacy Policy?
4. Can the feature work with less data?

If any answer is "I'm not sure", the data collection does not ship.

### 10.3 Consent Standards

Consent language must be:
- Plain English — no legal jargon
- Specific — explains exactly what is being consented to
- Separate — never bundled with Terms of Service
- Withdrawable — every consent has a clear revocation path in Settings

```
BAD — bundled, vague
"By continuing, you agree to our Terms and Privacy Policy."

GOOD — specific, standalone
"To create your future self image, PRLifts will:
• Send your photo to our image generation service (Fal.ai)
• Delete your original photo within 60 seconds
• Store only the generated image, which you own

You can delete this image at any time from Settings.
[Agree] [No thanks]"
```

### 10.4 Biometric Data Rules

These apply specifically to the future self feature:
- Photo is never written to disk — received, forwarded, deleted within 60 seconds
- No logging of photo content — only metadata (user_id, duration_ms, job_id)
- BiometricConsent record is created before any photo is processed
- If the BiometricConsent write fails for any reason, the photo processing request is
  rejected immediately. No photo is processed without a confirmed consent record.
  The user is returned to the consent screen — consent is not retried silently.
- BiometricConsent is backend-write-only — no client writes permitted via RLS
- Fal.ai DPA must be executed before any photo is processed in any environment

### 10.5 Data Subject Request Standard

Users can request data deletion or access via:
- In-app: Settings → Account → Delete Account
- Email: privacy@prlifts.app — acknowledged within 72 hours, fulfilled within 30 days

Every request is logged in `data_subject_requests` table and verified complete
before closing.

---

## 11. Definition of Done

A piece of work is Done only when ALL of the following are true:

**Code quality:**
- [ ] Tests written and passing
- [ ] Coverage at or above 90% for changed code
- [ ] No new linting violations (SwiftLint / Ruff)
- [ ] No mypy type errors (Python)
- [ ] No function over 40 lines of implementation logic
- [ ] All public functions have docstrings/doc comments
- [ ] Module header comment is accurate and up to date

**Standards compliance:**
- [ ] No TODO/FIXME comments without a GitHub issue number
- [ ] No commented-out code
- [ ] No hardcoded secrets, PII, or sensitive data
- [ ] All user-facing copy follows voice and tone standards
- [ ] All new UI elements have accessibility annotations

**Process:**
- [ ] PR description explains what changed and why
- [ ] ARCHITECTURE.md updated if any architectural decision was made
- [ ] GitHub issue acceptance criteria are all satisfied
- [ ] Security review checklist completed if the feature touches user data
- [ ] Data minimisation question answered if new data collection was added

---

## 12. Tooling Enforcement Summary

| Tool | What it checks | Enforcement level |
|---|---|---|
| SwiftLint | Swift style, naming, complexity | CI blocks merge |
| Ruff | Python linting and formatting | CI blocks merge |
| mypy | Python type annotations | CI blocks merge |
| pip audit | Python dependency vulnerabilities | CI blocks merge |
| Xcode coverage | iOS coverage >= 90% | CI blocks TestFlight |
| pytest-cov | Backend coverage >= 90% | CI blocks merge |
| Prompt evaluation (body image) | Harmful framing in AI prompts | CI blocks merge |
| Prompt evaluation (other) | Accuracy, tone, constraints | CI informational |
| Secret scanning | Hardcoded secrets in code | CI blocks merge |
| pre-commit hooks | Local enforcement before push | Developer workstation |

**CODEOWNERS entries requiring designated review:**
- `config/ai_forbidden_phrases.txt` — requires content review
- `tests/prompt_evaluation/` — requires content review
- `docs/ARCHITECTURE.md` — requires principal engineer review
- `docs/STANDARDS.md` — requires domain lead review for changed section

---

*This document is owned by the full engineering standards panel.*
*Changes to any section should be reviewed by the relevant domain lead before merging.*
*When in doubt: if it is not in this document, ask before assuming.*
