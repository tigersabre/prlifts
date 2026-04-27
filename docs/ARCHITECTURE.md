# PRLifts — Architecture Document

**Version:** 1.3  
**Status:** Living document — all changes must be logged in the Decision Log  
**Last updated:** April 2026 — updated following 10-specialist panel review (rounds 1, 2, 3, and final)

---

## Table of Contents

1. [Overview](#overview)
2. [Platform](#platform)
3. [Engineering Principles](#engineering-principles)
4. [Phased Roadmap](#phased-roadmap)
5. [Tech Stack](#tech-stack)
6. [Architecture Layers](#architecture-layers)
7. [Infrastructure](#infrastructure)
8. [Testing Strategy](#testing-strategy)
9. [Security](#security)
10. [Data Model](#data-model)
11. [Open Decisions](#open-decisions)
12. [Development Workflow](#development-workflow)
13. [Project Tracking](#project-tracking)
14. [Decision Log](#decision-log)

---

## Overview

PRLifts is an iOS fitness tracking journal for weightlifting and cardio. The core value proposition is frictionless workout logging combined with meaningful AI-powered feedback. Users can log ad hoc sessions or follow structured programs, track body metrics and steps, and receive contextual feedback on their progress relative to their own history and population benchmarks.

PRLifts has two differentiators that separate it from every other fitness logging app:

**The AI feedback layer.** Most fitness apps are logging tools. PRLifts uses logged data to generate genuinely useful observations — PR detection, volume trends, comparative benchmarking, and weekly summaries — that give users a reason to keep logging.

**The future self vision board.** During onboarding, users provide a photo and a goal. PRLifts generates a realistic AI image of them looking fit, healthy, and strong — a personalised vision of where they are headed. This image becomes the emotional anchor of the entire motivational system. It appears on their vision board in the app, and is attached to show-up nudge notifications on days they are scheduled to train but haven't started yet. The message is always the same: this is where you are going — just show up today. The combination of a personalised future self image and a tiny habits framing — lowering the ask to the smallest possible action — addresses the hardest problem in fitness: not knowledge or programming, but showing up when motivation is low.

---

## Platform

**V1:** iOS + iPadOS only.

iPadOS comes for free with SwiftUI layout adaptations. Android is deferred until product-market fit is established. The iOS ecosystem — HealthKit, Apple Watch, Sign in with Apple — provides meaningful advantages for a fitness app that justify iOS-first focus.

Building cross-platform from V1 would deliver 80% of both platforms instead of 100% of either, and would significantly complicate the HealthKit and Apple Watch integrations planned for V3.

Android becomes a viable conversation after V2 ships. The backend-first architecture ensures the API is platform-agnostic when that time comes.

---

## Engineering Principles

**Right-sized architecture, not minimal architecture.** MVP feature set, production-grade structure from day one. No over-engineering for features that don't exist yet. No under-engineering that forces rewrites later.

**Business logic lives in the Core Library, not the app.** The iOS app is a thin UI layer. All domain logic — workout models, PR detection, AI service interfaces, data parsing — lives in the Swift Package. This enforces testability and makes future platform expansion straightforward.

**The backend is an API, not an iOS backend.** The iOS app is one client of the backend, not the only possible client. Design endpoints as platform-agnostic resources.

**Dependency injection throughout.** The AI provider, exercise library API, and auth provider are all injected interfaces. Swapping implementations — a different AI provider, a different exercise API — requires no changes to consuming code.

**Nothing is Done until it has tests.** Acceptance criteria are written before implementation begins. Tests ship with the feature in the same PR. The test suite is the regression net for every subsequent feature.

**The architecture document is the source of truth.** Decisions agreed in conversation must be recorded here before implementation proceeds. When Claude produces output that contradicts this document, this document wins.

**Structured logging from day one.** Every backend API log emits JSON with a consistent shape: `user_id`, `endpoint`, `duration_ms`, `status_code`, `error_code`. Retrofitting structure into unstructured logs is painful. Aggregation platform is deferred to V2 — the structure is not.

**API contract is a committed file, not a live endpoint.** The OpenAPI spec (`openapi.json`) is generated from FastAPI on every CI build and committed to the repo. A change to the spec without a version bump fails CI. The spec is the contract — not the auto-docs endpoint.

**AI operations are asynchronous.** No AI call (Claude API or Fal.ai) runs synchronously in a request/response cycle. All AI operations use FastAPI BackgroundTasks in V1, with a status polling endpoint for the client. This prevents timeouts and decouples AI latency from user-facing response time.

**Conflict resolution uses server timestamps.** The client sends `client_created_at` for context. The server assigns `server_received_at`. Server timestamps govern conflict resolution in last-write-wins scenarios. Client clocks are never trusted for ordering.

---

## Phased Roadmap

### V1 — MVP

The core loop: log a workout, see your history, get one AI insight, hit a PR and know about it.

**Mobile:** Auth, ad hoc workout logging, cardio logging, exercise library (ExerciseDB), workout history, PR auto-detection, AI insight per workout.

**Core Library:** Workout models, AI service interface, data parser, exercise models.

**Backend:** REST API, auth service, PostgreSQL, basic AI service.

**External:** ExerciseDB, AI provider, Sign in with Apple, Google auth.

### V2 — Depth

**Mobile:** Program builder, body metrics, spreadsheet import, progress charts, benchmarking.

**Core Library:** Program models, metrics models, CSV parser.

**Backend:** Advanced AI (weekly summaries, trend analysis, comparative benchmarking), analytics engine.

**Infrastructure:** Cloudflare R2 for progress photo storage, log aggregation platform, load testing, contract tests.

### V3 — Integrations

**Mobile:** HealthKit sync, Apple Watch companion.

**Core Library:** HealthKit bridge, Watch session manager.

**Backend:** Wearable data ingestion service, webhook endpoints for Garmin, Whoop, Oura.

**External:** Apple HealthKit, Garmin, Whoop, Oura.

### V4 — Social and Monetisation

**Mobile:** Social sharing, coach view.

**Backend:** Social graph, premium/billing, audit logging.

**External:** Stripe, payment processor.

---

## Tech Stack

### iOS App
- **Language:** Swift
- **UI framework:** SwiftUI
- **Local persistence:** SwiftData (offline-first)
- **Dependency management:** Swift Package Manager
- **Testing:** XCTest (unit), XCUITest (UI), snapshot tests (V2)

### Core Library
- **Type:** Swift Package (SPM)
- **Scope:** All domain models, business logic, service interfaces, data parsers
- **Dependency on app layer:** None — the library has no knowledge of UIKit or SwiftUI

### Backend
- **Language:** Python
- **Framework:** FastAPI
- **API style:** REST, versioned under `/v1/`
- **Task scheduler:** APScheduler (AsyncIOScheduler) — in-process recurring tasks (job expiry cleanup every 60s)
- **Database:** PostgreSQL via Supabase
- **Auth:** Supabase Auth (Sign in with Apple, Google, email/password)
- **Storage:** Supabase Storage (V1), Cloudflare R2 (V2)
- **Hosting:** Railway (staging + production environments)
- **Rate limiting:** Upstash Redis via FastAPI middleware
- **Text AI provider:** Anthropic Claude API
- **Image AI provider:** Fal.ai (future self generation)
- **AI access:** All AI calls made from backend only — API keys never touch the iOS app

### CI/CD
- **iOS pipeline:** Xcode Cloud (build, test, archive, distribute to TestFlight)
- **Backend pipeline:** GitHub Actions (lint, test, build) → Railway (auto-deploy)
- **Source control:** GitHub (monorepo)

### Observability
- **Crash and error reporting:** Sentry (iOS + backend)
- **Request logs:** Railway (structured JSON)
- **Database dashboard:** Supabase Studio
- **Product analytics:** PostHog (V1)
- **Log aggregation:** TBD platform (V2)

---

## Architecture Layers

```
┌─ Mobile App — iOS + iPadOS (SwiftUI) ──────────────────────┐
│  Thin UI layer — no business logic                          │
│  Consumes Core Library exclusively                          │
│  Never calls backend directly                               │
└────────────────────────┬───────────────────────────────────┘
                         ↕
┌─ Core Library — Swift Package Manager ─────────────────────┐
│  All domain models, business logic, service interfaces      │
│  Platform-agnostic — no UIKit, no SwiftUI                   │
│  Fully unit testable without a simulator                    │
└────────────────────────┬───────────────────────────────────┘
                         ↕
┌─ Backend — REST API + Services ────────────────────────────┐
│  Platform-agnostic API                                      │
│  iOS is one client, not the only possible client            │
│  Supabase: PostgreSQL + Auth + Storage                      │
│  Railway: API server + AI service layer                     │
└────────────────────────┬───────────────────────────────────┘
                         ↕
┌─ External Services ────────────────────────────────────────┐
│  ExerciseDB · AI provider · Sign in with Apple              │
│  Google auth · HealthKit (V3) · Wearables (V3)              │
│  Stripe (V4)                                                │
└────────────────────────────────────────────────────────────┘
```

**The architectural rule:** Each layer only communicates with the layer directly adjacent to it. The mobile app never calls external services directly. The Core Library never calls the backend directly. Violations of this rule require an explicit decision log entry.

---

## Infrastructure

### Source Control
**GitHub** — monorepo containing iOS app, Swift Package, backend, and shared CI config. One repo, one issue tracker, one PR workflow.

### iOS Pipeline
```
GitHub → Xcode Cloud (build + XCUITest) → TestFlight → App Store Connect
```
- Xcode Cloud triggers on push to `main`
- Full test suite must pass before TestFlight distribution
- WatchKit target added to existing workflow in V3

**TestFlight tiers:**

| Tier | Who | Limit | Review required |
|---|---|---|---|
| Internal | You + Apple Developer account members | 25 people | No |
| External | Broader beta group, invite by email or public link | 10,000 people | Yes — first build only |

Internal testers receive builds automatically on every green Xcode Cloud run. External testers receive builds on manual promotion. Both tiers receive the same binary — feature access is controlled by `beta_tier` on User and PostHog feature flags, not by the build.

### Backend Pipeline
```
GitHub → GitHub Actions (lint + test + build) → Railway staging → Railway production
```
- GitHub Actions triggers on every PR
- All tests must pass before merge
- Merge to `develop` auto-deploys to Railway staging
- Promotion to production is manual
- Never push directly to production
- **Railway always-on enabled before public launch** — cold starts during onboarding AI flow are unacceptable

### Secret Management

All secrets stored in Railway environment variables. No secrets in code, `.env` files, or committed to the repo.

| Secret | Where stored | Rotation procedure |
|---|---|---|
| Anthropic Claude API key | Railway env var | Rotate in Anthropic dashboard → update Railway → restart service |
| Fal.ai API key | Railway env var | Rotate in Fal.ai dashboard → update Railway → restart service |
| Supabase service key | Railway env var | Rotate in Supabase dashboard → update Railway → restart service |
| Supabase JWT secret | Railway env var | Requires coordinated rotation with all active sessions |
| Upstash Redis URL + token | Railway env var | Rotate in Upstash dashboard → update Railway → restart service |
| Sentry DSN | Railway env var + Xcode Cloud env var | Update in both on rotation |

Pre-launch secrets audit: verify no secrets are in git history, `.env` files, or hardcoded strings before first public build.

### Runtime Services

| Service | Purpose | Phase |
|---|---|---|
| Supabase | PostgreSQL + Auth + Storage | V1 |
| Railway | API server + AI service layer | V1 |
| Upstash Redis | Rate limiting counter store + job status caching | V1 |
| Cloudflare R2 | Progress photo storage at scale | V2 |
| Stripe | Premium subscriptions + billing | V4 |

### Observability

| Tool | Purpose | Phase |
|---|---|---|
| Sentry | iOS crash reports + backend error tracking | V1 |
| Railway logs | Structured request logs + deploy history | V1 |
| Supabase Studio | DB dashboard + query inspector + auth logs | V1 |
| PostHog | Product analytics + funnel analysis | V1 |
| Log aggregation platform | Queryable log history + dashboards | V2 |

### Alerting Thresholds

Configured in Sentry and Railway before public launch:

| Metric | Threshold | Action |
|---|---|---|
| Backend error rate | > 1% over 5 minutes | Sentry alert → email |
| Railway CPU | > 80% for 5 minutes | Railway alert → email |
| Supabase connection pool | > 80% utilization | Supabase alert → email |
| AI endpoint latency | > 10s p95 | Sentry alert → email |
| Daily AI spend | > defined threshold | Auto-disable `ai_insights_enabled` flag |
| iOS crash-free rate | < 99% | Sentry alert → email |

### Runbook

Written before public launch. Covers:
- How to rollback a Railway deployment to a previous build
- How to restore Supabase from point-in-time backup (tested once during V1 development)
- How to rotate each API key (Claude, Fal.ai, Supabase, Sentry) without downtime
- How to manually disable a PostHog feature flag in an emergency
- How to force-disable the future self feature if App Store compliance issue arises
- Railway log retention period: documented and set before launch (default is short)

### Feature Flags

Managed via PostHog — no additional tool needed. Flags are evaluated per user or cohort from the PostHog dashboard. Toggling a flag requires no code change and no new build.

**V1 flags:**

| Flag | Purpose | Default |
|---|---|---|
| `premium_features_enabled` | Grants full premium access — used for beta testers and V1 launch period unlock | off |
| `future_self_enabled` | Gates AI image generation independently — allows cost control during beta | off |
| `ai_insights_enabled` | Gates AI workout feedback independently | off |

**Access control hierarchy** — two layers checked in order:

1. **PostHog flag** — checked first. If the flag is on for this user or cohort, feature is accessible.
2. **`beta_tier` on User** — database-level override. `full_access` grants all premium features regardless of PostHog flags. Used when PostHog is unavailable or for guaranteed access without cohort management.

**Beta rollout workflow:**
```
Build passes Xcode Cloud
      ↓
Auto-distributed to internal TestFlight testers
      ↓
You test and verify
      ↓
Enable PostHog flag for external beta cohort
      ↓
External testers get feature access
      ↓
Confident → promote to App Store production
```

### Field Debugging

Three areas where the architecture creates debugging complexity, with explicit workarounds built in from V1.

**1. Offline-first sync visibility**

The failure mode: user reports a missing workout. The question is whether it failed to write locally, failed to sync, or was overwritten by conflict resolution. Without visibility into the sync process, this is undiagnosable remotely.

Workaround — **sync event log:**
- Local SwiftData table recording every write attempt, sync attempt, conflict resolution, and sync success or failure with timestamp
- Automatically uploaded to backend on sync failure
- Uploadable on demand when user taps "Report a problem"
- Readable in Supabase Studio once uploaded

**2. PII-free logs create user correlation problem**

The failure mode: user contacts support with a problem. You cannot search Sentry or Railway logs by email or name — PII is stripped. You have no way to find their logs without their anonymous user ID.

Workaround — two tools:
- **In-app problem reporter** — captures anonymous user ID, device info, iOS version, problem description, and optional sync event log upload. Sends to a support inbox. Now you have the ID.
- **User ID lookup** — simple admin Supabase query mapping email → anonymous user ID. Used only in admin context when a user contacts support directly. Never exposed in general logs.

**3. AI response quality visibility**

The failure mode: user reports the AI gave incorrect or strange feedback. No record exists of what prompt was sent or what was returned unless explicitly logged.

Workaround — **AI request/response log table:**
- Separate access-controlled table in Supabase
- Stores: prompt, response, user ID, endpoint, timestamp
- 30-day retention with automatic deletion
- Never appears in Sentry, Railway logs, or general observability tooling
- Used exclusively for diagnosing AI quality issues

**SwiftData migration safety**

Every SwiftData migration writes a version flag to UserDefaults before starting and clears it on completion. If the app launches and finds a pre-migration flag without a post-migration flag, a migration failed mid-run. The app surfaces a recovery flow rather than silently operating on potentially corrupted local data.

**Offline sync trigger points**

SwiftData sync to backend fires on these explicit triggers — not on an arbitrary timer:
1. **App foreground** — on every `scenePhase` transition to `.active` (primary trigger)
2. **Connectivity restored** — `NWPathMonitor` detects network path becoming `.satisfied` (primary trigger)
3. **Background refresh** — `BGAppRefreshTask` registration, fires when iOS grants background time. **This is opportunistic and not guaranteed.** Background refresh must be declared in Info.plist and can be disabled by the user in iOS Settings. The sync architecture does not depend on this trigger — it is registered as a best-effort bonus. Never assume it fires reliably.
4. **Force-quit recovery** — on next app launch, SyncEventLog is checked for `uploaded_at: null` entries representing unsynced data from the previous session. These are re-queued before any new data is written.

Sync is idempotent — re-sending a record that already exists on the backend is a no-op (upsert on `id`). The backend never creates duplicates from a re-sync.

### Backup and Disaster Recovery
Supabase point-in-time recovery is enabled from day one. The free tier provides a 24-hour recovery window. Upgrade to Supabase Pro ($25/month) before public App Store launch for a 7-day recovery window. Railway provides deployment rollback to any previous build with zero downtime. Restore process tested once during V1 development before public launch.

---

## Testing Strategy

**The principle:** Nothing is marked Done until it has tests that prove it works and will continue to work as subsequent features are added.

**Acceptance criteria are written before implementation begins** — not after. This ensures tests verify intended behavior, not just describe what the code happens to do.

**Coverage target: 90% on all business logic.** Enforced by CI on both iOS and backend pipelines. A PR that drops coverage below 90% on the Core Library or backend business logic layer cannot merge.

### iOS Testing

| Type | Scope | Tool | Phase |
|---|---|---|---|
| Unit tests | Core Library — models, parsing, PR logic, AI interface | XCTest + Swift Testing | V1 |
| UI tests | Critical flows — login, log workout, view history, PR notification | XCUITest | V1 |
| Accessibility | VoiceOver labels, Dynamic Type, 44pt touch targets on all interactive elements | XCTest + manual | V1 |
| Coverage reporting | Core Library coverage after every run, 90% threshold enforced | Xcode native coverage | V1 |
| CI gate | Full test suite on every push, blocks TestFlight on failure | Xcode Cloud | V1 |
| Snapshot tests | Catch unintended UI regressions on key screens | V2 | V2 |
| Performance tests | XCTest metrics on heavy data loads — long workout history | XCTest | V2 |

### iOS Mocking Strategy

Protocol-based dependency injection is the primary mocking approach — no third party mocking framework needed. Every external dependency (AI provider, backend API, ExerciseDB) is defined as a Swift protocol. Production code receives real implementations. Test code receives mock implementations.

```swift
// Protocol defined in Core Library
protocol AIProviderProtocol {
    func generateInsight(workout: Workout) async throws -> String
}

// Production
let service = WorkoutInsightService(aiProvider: ClaudeProvider())

// Test
let service = WorkoutInsightService(aiProvider: MockAIProvider())
```

**Swift Testing** (Apple's native framework, 2024) used alongside XCTest for test doubles and argument capture. No third party mocking frameworks (Cuckoo, Mockito) — Swift Testing covers all V1 needs natively.

### Backend Testing

| Type | Scope | Tool | Phase |
|---|---|---|---|
| Unit tests | Business logic — AI service, PR calculation, data transforms | pytest | V1 |
| Integration tests | Full request/response cycle against test database | pytest + httpx | V1 |
| Coverage reporting | Coverage report after every run, 90% threshold enforced in CI | pytest-cov | V1 |
| CI gate | All tests must pass and coverage ≥ 90% before PR can merge | GitHub Actions | V1 |
| Load tests | Stress-test workout log and AI endpoints | k6 | V2 |
| Contract tests | Verify iOS ↔ backend API contract on every build | schemathesis | V2 |

### Offline Sync Test Matrix

The offline-first sync is the highest-complexity V1 feature. These scenarios must have explicit XCTest integration tests:

1. Write offline → come online → verify data synced to backend
2. Write offline → different write from another device online → verify last-write-wins (server timestamp) resolves correctly
3. Sync failure → verify SyncEventLog entry created with correct event_type
4. App force-quit mid-sync → verify recovery on next launch without data loss
5. SwiftData migration fails mid-run → verify UserDefaults flag detected → recovery flow surfaces

### AI Feature Test Cases

These must be explicitly tested — not left as happy-path only:

1. AI provider returns error → app degrades gracefully, user sees appropriate message, no crash
2. Image quality gate: both generated variations score below 6/10 → fallback message shown, no poor image displayed
3. Rate limit hit on AI endpoint → appropriate user-facing message, request not silently dropped
4. Job polling: job completes while app is backgrounded → result available on foreground
5. Photo deletion: **automated integration test in CI** verifies photo is absent from all storage locations within 60 seconds of generation — tagged `@security`, runs on every push
6. Job expiry: job not completed within 5 minutes → APScheduler cleanup task sets status to `expired` → client receives fallback message on next poll
7. BiometricConsent absent → future self feature blocked, appropriate message shown, no bypass possible
8. APScheduler cleanup task unit test: jobs with `expires_at < now()` in `pending` or `processing` state are set to `expired`; jobs not yet expired are untouched
9. APScheduler cleanup integration test: scheduler is registered on FastAPI startup, cleanup function is invoked on schedule
10. Quality gate scoring failure (Claude vision call fails) → fail-closed: fallback message shown, first Fal.ai variation not displayed, `quality_score: null` logged in AIRequestLog

**pytest-mock** — wraps Python's standard `unittest.mock` with cleaner pytest fixture integration. Used for unit-level mocking of database calls, AI provider responses, and external service calls.

**httpx mock transport** — mocks HTTP-level responses from external APIs (Claude API, Fal.ai, ExerciseDB) without making real network calls. Keeps unit tests fast, deterministic, and free of external dependencies.

```python
# Example — mocking Claude API response in a unit test
def test_workout_insight_generation(mock_claude_client):
    mock_claude_client.return_value = "You hit a new bench PR this session."
    result = insight_service.generate(workout)
    assert "bench PR" in result
```

### Reporting

| What | Tool | When |
|---|---|---|
| iOS build status | Xcode Cloud dashboard + email | On every push |
| iOS test results | Xcode Cloud test report | On every push |
| iOS coverage report | Xcode native coverage in App Store Connect | On every push |
| Backend PR status | GitHub Actions check on PR | On every PR |
| Backend test results | pytest output in GitHub Actions log | On every PR |
| Backend coverage report | pytest-cov summary in GitHub Actions | On every PR |
| Production crashes | Sentry email + dashboard | On occurrence |
| User behaviour | PostHog dashboard | Ongoing |
| Database health | Supabase Studio | On demand |
| API health | Railway logs | On demand |

### The Development Loop

Every component follows this sequence before being marked Done:

1. Agree on approach and acceptance criteria
2. Implement component and tests together in Claude Code
3. Run tests — confirm green
4. Confirm coverage at or above 90%
5. Walk through what was built and why
6. Close GitHub issue

---

## Security

### Auth and Access

| Control | Detail | Phase |
|---|---|---|
| Supabase JWT | Short-lived tokens, automatic refresh | V1 |
| Row Level Security | DB-enforced — users can only read their own rows | V1 |
| Keychain storage | Auth tokens stored in iOS Keychain, never UserDefaults | V1 |
| SSL certificate pinning | TrustKit pinning on iOS for backend connection — pins to CA certificate (not leaf), includes backup pin, rotation procedure in runbook — gym WiFi is adversarial | V1 |
| Coach role + audit log | Scoped read access, every access recorded | V4 |

### Data and Transport

| Control | Detail | Phase |
|---|---|---|
| Encrypted at rest | Supabase + Railway enforce AES-256 by default | V1 |
| TLS 1.3 in transit | Enforced by Railway + Supabase, no HTTP fallback | V1 |
| No PII in logs | Sentry scrubbing rules strip email, name, health data | V1 |
| Photo data minimization | User photo received by backend, forwarded to Fal.ai immediately, never written to disk, never logged. Deleted from all systems within 60 seconds of image generation. | V1 |
| GDPR — export + delete | User data export endpoint + full account deletion | V2 |

### API and iOS Surface

| Control | Detail | Phase |
|---|---|---|
| Rate limiting — AI endpoints | Max 10 requests/minute per user (Claude + Fal.ai combined) | V1 |
| Rate limiting — auth endpoints | Max 5 attempts/minute per IP | V1 |
| Rate limiting — workout log | Max 100 requests/minute per user | V1 |
| Rate limit enforcement | FastAPI middleware with Redis as counter store | V1 |
| Input validation | Strict schema validation on every inbound payload | V1 |
| Apple Privacy Manifest | Required for App Store — declares all data usage | V1 |
| API versioning | All endpoints under `/v1/` from day one | V1 |
| OpenAPI spec | `openapi.json` committed to repo, generated on every CI build, drift fails CI | V1 |
| Penetration testing | Third-party pen test before public launch | V2 |
| HealthKit entitlements | Scoped read-only access, user-granted per data type | V3 |

### Biometric Data and Legal Compliance

The future self feature processes user photos through Fal.ai. This constitutes biometric data processing under Illinois BIPA, Texas CUBI, and analogous state laws, and falls under GDPR Article 9 as special category data.

**Hard prerequisites before the future self feature ships:**
- Explicit written BIPA consent obtained separately from general privacy policy
- Data Processing Agreement (DPA) executed with Fal.ai
- Standard Contractual Clauses (SCCs) in place if Fal.ai processes outside EU/EEA
- Photo deletion policy enforced in code: photo deleted within 60 seconds of generation, verified by automated CI test tagged `@security`
- Biometric data retention schedule disclosed in privacy policy
- Privacy policy reviewed by attorney before V1 launch (not just before App Store submission)

**BiometricConsent RLS policy:**
BiometricConsent table has Row Level Security with `user_id = auth.uid()` for reads. Write access is backend-only via the service role key — no direct client writes permitted. Users cannot create, modify, or delete their own consent records directly. This ensures the audit record cannot be tampered with from the client.

**Note on ip_country for BIPA scoping:**
The `ip_country` field on BiometricConsent records the country at time of consent. This is a useful signal but not a reliable BIPA scoping mechanism — BIPA applies to Illinois residents regardless of IP location (a Chicago resident using a VPN appears non-Illinois). The privacy policy and consent flow must treat all users as potentially subject to BIPA rather than attempting to scope by IP. The field is retained for analytics only.

---

## Data Model

### User
```
id                  uuid          primary key
email               string        unique, nullable — Apple Sign In may not provide one
display_name        string        nullable
avatar_url          string        nullable
unit_preference     enum          kg | lbs
measurement_unit    enum          cm | inches    default cm
date_of_birth       date          nullable
gender              enum          male | female | na    default na
goal                enum          build_muscle | lose_fat | improve_endurance |
                                  athletic_performance | general_fitness    nullable
beta_tier           enum          none | tester | full_access    default none
created_at          timestamp
updated_at          timestamp
```

Notes: `email` is nullable because Sign in with Apple allows relay addresses or no email. `gender` defaults to `na` — no feature is gated on it. `measurement_unit` is a display preference only — all measurements stored internally in cm. `beta_tier` provides database-level access control independent of PostHog feature flags. `goal` is nullable — collected during Phase 2 onboarding (post-first-workout) and drives future self image generation prompt. Never required to use the core app.

---

### Exercise
```
id                      uuid          primary key
name                    string        unique
category                enum          strength | cardio | flexibility | bodyweight |
                                      mobility | saq | rehab
muscle_group            enum          upper_chest | mid_chest | lower_chest |
                                      upper_back | lower_back | shoulders |
                                      biceps | triceps | quads | hamstrings |
                                      calves | glutes | abs | obliques | full_body
secondary_muscle_groups enum[]        nullable array — same enum values as muscle_group
equipment               enum          barbell | dumbbell | kettlebell | machine |
                                      cable | bodyweight | cardio_machine | other
instructions            string        nullable
demo_url                string        nullable — ExerciseDB gif or video
is_custom               boolean       default false
created_by              uuid          nullable — foreign key to User, null if from ExerciseDB
created_at              timestamp
updated_at              timestamp
```

Notes: `is_custom: false` + `created_by: null` = ExerciseDB canonical exercise. `is_custom: true` + `created_by: user_id` = user-created. `secondary_muscle_groups` uses PostgreSQL native array type — no junction table needed.

**Enum migration note (V2):** `muscle_group`, `category`, and `equipment` are defined as PostgreSQL enums in V1. PostgreSQL enums require a migration to add values and can lock tables. These three fields are flagged for conversion to lookup tables in V2 before the exercise library grows significantly. `status`, `weight_modifier`, `record_type`, `unit_preference`, and `gender` remain as enums — these are stable and enum semantics are appropriate for them.

---

### Workout
```
id                uuid          primary key
user_id           uuid          foreign key to User
name              string        nullable — null for ad hoc sessions
notes             string        nullable
status            enum          in_progress | paused | partial_completion | completed
type              enum          ad_hoc | planned
format            enum          weightlifting | cardio | mixed | other
plan_id           uuid          nullable — foreign key to WorkoutPlan (V2)
started_at        timestamp
completed_at      timestamp     nullable
duration_seconds  integer       nullable — stored explicitly for query performance
location          enum          gym | home | outdoor | other    nullable
rating            integer       nullable — 1 to 5, user subjective session rating
created_at        timestamp
updated_at        timestamp
```

Notes: `duration_seconds` is derivable from `completed_at - started_at` but stored explicitly for query performance. `name` is nullable — app displays "Workout — [date]" when null. `partial_completion` distinguishes genuinely unfinished sessions from abandoned ones.

---

### WorkoutExercise
```
id                uuid          primary key
workout_id        uuid          foreign key to Workout
exercise_id       uuid          foreign key to Exercise
order_index       integer       position within the workout
notes             string        nullable — exercise-level observations for this session
rest_seconds      integer       nullable — target rest between sets
created_at        timestamp
updated_at        timestamp
```

Notes: Junction entity between Workout and Exercise. `order_index` preserves the sequence exercises were performed. `rest_seconds` lives here rather than WorkoutSet because rest is typically consistent across sets of a given exercise.

---

### WorkoutSet
```
id                    uuid          primary key
workout_exercise_id   uuid          foreign key to WorkoutExercise
set_number            integer       order within the exercise
set_type              enum          normal | warmup | dropset | failure | pr
weight                decimal       nullable — for loaded exercises (barbell, dumbbell etc)
weight_unit           enum          kg | lbs    nullable
weight_modifier       enum          none | assisted | weighted    default none
modifier_value        decimal       nullable — assistance or added load amount
modifier_unit         enum          kg | lbs    nullable
reps                  integer       nullable — null for duration-based sets
duration_seconds      integer       nullable — null for rep-based sets
distance_meters       decimal       nullable — for cardio sets
calories              integer       nullable — estimated calories for this set
rpe                   integer       nullable — Rate of Perceived Exertion 1 to 10
is_completed          boolean       default false
notes                 string        nullable
created_at            timestamp
updated_at            timestamp
```

Notes: `weight_modifier` handles bodyweight exercise variants — `none` = pure bodyweight, `assisted` = machine assistance (modifier_value subtracted from effective load), `weighted` = added load (modifier_value added to bodyweight). `weight_unit` stored per set so historical records remain accurate if user changes unit preference. `set_type: pr` is system-set by PR detection, never user-set. `is_completed` supports pre-populated sets from WorkoutPlan in V2.

---

### PersonalRecord
```
id                    uuid          primary key
user_id               uuid          foreign key to User
exercise_id           uuid          foreign key to Exercise
workout_set_id        uuid          foreign key to WorkoutSet
weight_modifier       enum          none | assisted | weighted
record_type           enum          heaviest_weight | most_reps | longest_duration |
                                    longest_distance | best_rpe
value                 decimal
value_unit            enum          kg | lbs | reps | seconds | meters    nullable
recorded_at           timestamp
previous_value        decimal       nullable
previous_recorded_at  timestamp     nullable
created_at            timestamp
updated_at            timestamp
```

Notes: System-generated only — never user-created. Triggered automatically when a WorkoutSet is marked completed. `weight_modifier` ensures weighted pull-up PRs and bodyweight pull-up PRs are tracked separately. `previous_value` and `previous_recorded_at` stored directly for AI feedback performance — avoids complex historical queries.

---

### Database Indexes

Required indexes defined in the initial migration. These are not afterthoughts — missing indexes at small scale are invisible and catastrophic at scale.

```sql
-- Workout history by user (most common query)
CREATE INDEX idx_workout_user_started ON workout(user_id, started_at DESC);

-- PR lookup by user and exercise
CREATE INDEX idx_pr_user_exercise ON personal_record(user_id, exercise_id);

-- Exercise search by name
CREATE INDEX idx_exercise_name ON exercise(name);

-- WorkoutExercise ordering within a workout
CREATE INDEX idx_workout_exercise_order ON workout_exercise(workout_id, order_index);

-- WorkoutSet ordering within a workout exercise
CREATE INDEX idx_workout_set_order ON workout_set(workout_exercise_id, set_number);

-- PR detection query — best performance for an exercise (runs on every set completion)
CREATE INDEX idx_workout_set_pr_detection ON workout_set(workout_exercise_id, weight, reps);

-- Job polling by user (client polls frequently during AI operations)
CREATE INDEX idx_job_user_status ON job(user_id, status, created_at DESC);

-- Job monthly usage count for cost controls (checks per-user monthly limits before each AI job)
CREATE INDEX idx_job_user_type_month ON job(user_id, job_type, created_at DESC);

-- Job expiry cleanup (runs every minute, partial index on in-progress jobs only)
CREATE INDEX idx_job_expires ON job(expires_at) WHERE status IN ('pending', 'processing');

-- AI request log expiry cleanup
CREATE INDEX idx_ai_log_expires ON ai_request_log(expires_at);

-- Sync event log upload status
CREATE INDEX idx_sync_log_upload ON sync_event_log(user_id, uploaded_at);
```

---

### WorkoutPlan (V2)
```
id                uuid          primary key
user_id           uuid          foreign key to User
name              string
description       string        nullable
duration_weeks    integer
days_per_week     integer
format            enum          weightlifting | cardio | mixed | other
difficulty        enum          beginner | intermediate | advanced
is_active         boolean       default false — one active plan per user at a time
is_custom         boolean       default true
source            enum          in_app | spreadsheet_import | template
started_at        timestamp     nullable
completed_at      timestamp     nullable
created_at        timestamp
updated_at        timestamp
```

---

### WorkoutPlanDay (V2)
```
id                uuid          primary key
plan_id           uuid          foreign key to WorkoutPlan
week_number       integer
day_number        integer       1 through 7
name              string        nullable
notes             string        nullable
is_rest_day       boolean       default false
created_at        timestamp
updated_at        timestamp
```

---

### WorkoutPlanExercise (V2)
```
id                uuid          primary key
plan_day_id       uuid          foreign key to WorkoutPlanDay
exercise_id       uuid          foreign key to Exercise
order_index       integer
sets              integer
reps              integer       nullable
duration_seconds  integer       nullable
distance_meters   decimal       nullable
rest_seconds      integer       nullable
notes             string        nullable
created_at        timestamp
updated_at        timestamp
```

Notes: WorkoutPlanExercise is the prescription. WorkoutExercise and WorkoutSet are the actuals. When a user starts a planned workout, the app pre-populates WorkoutExercise and WorkoutSet from the plan. The user logs actuals against those targets.

---

### BodyMetrics (V2)
```
id                uuid          primary key
user_id           uuid          foreign key to User
recorded_at       timestamp
weight            decimal       nullable
weight_unit       enum          kg | lbs    nullable
body_fat_percent  decimal       nullable
neck_cm           decimal       nullable
shoulders_cm      decimal       nullable
chest_cm          decimal       nullable
left_bicep_cm     decimal       nullable
right_bicep_cm    decimal       nullable
left_forearm_cm   decimal       nullable
right_forearm_cm  decimal       nullable
waist_cm          decimal       nullable
hips_cm           decimal       nullable
left_quad_cm      decimal       nullable
right_quad_cm     decimal       nullable
left_calf_cm      decimal       nullable
right_calf_cm     decimal       nullable
source            enum          manual | healthkit | withings | other
notes             string        nullable
created_at        timestamp
updated_at        timestamp
```

Notes: All measurement fields nullable — users may track only a subset. All measurements stored in cm regardless of `measurement_unit` preference on User — conversion is a display concern only. Left/right bilateral tracking enables imbalance detection in the AI layer.

---

### StepsEntry (V2)
```
id                uuid          primary key
user_id           uuid          foreign key to User
date              date          unique constraint on user_id + date
steps             integer       nullable
calories_burned   integer       nullable
calories_consumed integer       nullable
active_minutes    integer       nullable
distance_meters   decimal       nullable
source            enum          manual | healthkit | garmin | whoop | oura | other
created_at        timestamp
updated_at        timestamp
```

Notes: `date` not `timestamp` — steps and calories are daily aggregates. One row per user per day enforced by unique constraint. `calories_burned` and `calories_consumed` are distinct concepts — burned is activity output, consumed is dietary input.

---

### SyncEventLog (V1 — device-side)
```
id                uuid          primary key
user_id           uuid          foreign key to User
event_type        enum          write_attempt | sync_attempt | sync_success |
                                sync_failure | conflict_resolved
entity_type       enum          workout | workout_exercise | workout_set |
                                personal_record | body_metrics | steps_entry
entity_id         uuid          the local ID of the record involved
detail            string        nullable — error message or conflict resolution detail
occurred_at       timestamp
uploaded_at       timestamp     nullable — null until successfully uploaded to backend
```

Notes: Stored locally in SwiftData. Automatically uploaded to backend on sync failure. Uploadable on demand via in-app problem reporter. Readable in Supabase Studio once uploaded. Not a user-facing entity — internal debugging tool only.

---

### SupportReport (V1)
```
id                uuid          primary key
user_id           uuid          foreign key to User
device_model      string
ios_version       string
app_version       string
description       string
sync_log_uploaded boolean       default false
created_at        timestamp
```

Notes: Created when user taps "Report a problem." Captures anonymous user ID for log correlation, device context, and optional sync event log upload. Sent to support inbox. Never contains PII beyond what the user voluntarily writes in description.

---

### AIRequestLog (V1)
```
id                    uuid          primary key
user_id               uuid          foreign key to User
prompt_template_id    uuid          foreign key to PromptTemplate — which prompt version was used
endpoint              string        which AI feature generated this request
response              text          full response received
model                 string        Claude model version used
quality_score         decimal       nullable — face similarity score for future_self requests
duration_ms           integer       round trip time
job_id                uuid          nullable — foreign key to Job if async
created_at            timestamp
expires_at            timestamp     created_at + 30 days — auto-deleted after this
```

Notes: Stored in a separate access-controlled Supabase table. Never appears in Sentry, Railway logs, or general observability tooling. Used exclusively for diagnosing AI quality issues. 30-day retention enforced by a scheduled Supabase function. Access restricted to admin role only. `prompt_template_id` enables historical comparison of insight quality across prompt versions — this is what makes prompt A/B testing and rollback meaningful. `quality_score` records the face similarity score for future_self requests for quality gate analysis over time.

---

### PromptTemplate (V1)
```
id                uuid          primary key
feature           string        insight | future_self | benchmarking
version           string        v1.0, v1.1, etc
prompt_text       text          full prompt template with placeholders
is_active         boolean       default false — only one active per feature at a time
created_at        timestamp
deactivated_at    timestamp     nullable
```

Notes: Prompts are stored in the database, not in code. Every AIRequestLog row references the `prompt_template_id`. Enables prompt iteration without code deployment, A/B testing, rollback without a new build, and historical quality comparison. Only one prompt per feature can be active at a time.

---

### BiometricConsent (V1)
```
id                    uuid          primary key
user_id               uuid          foreign key to User
consent_given         boolean       true = explicitly accepted, false = declined
consent_timestamp     timestamp     server-assigned — never client clock
consent_version       string        version of the biometric consent policy accepted
policy_text_hash      string        SHA-256 of the exact consent text shown to user
ip_country            string        nullable — country code at time of consent for BIPA scoping
created_at            timestamp
```

Notes: Legal audit record of biometric consent. Required before `future_self_enabled` flag can be activated for a user. `consent_version` enables tracking when a policy change requires re-consent. `policy_text_hash` provides a tamper-evident record of exactly what the user agreed to. `consent_timestamp` is server-assigned — the client cannot manipulate the consent timestamp. One record per consent event per user — multiple records if consent is revoked and re-given.

---

### Job (V1)
```
id                uuid          primary key
user_id           uuid          foreign key to User
job_type          enum          insight | future_self | benchmarking
status            enum          pending | processing | complete | failed | expired
result            jsonb         nullable — populated on complete
error_message     string        nullable — user-facing message on failed or expired
created_at        timestamp
started_at        timestamp     nullable — when backend began processing
completed_at      timestamp     nullable — when job reached terminal state
expires_at        timestamp     created_at + 5 minutes — hung jobs auto-expire
```

Notes: Tracks async AI operations. Client polls `GET /v1/jobs/{id}` for status. Job expires after 5 minutes if not completed — a cleanup task runs every minute setting expired jobs to `expired` status. Client stops polling after 15 attempts with exponential backoff (2s initial, doubles each attempt, 10s maximum interval). On `expired` or `failed`, the client shows a defined fallback message — never a blank screen.

### Resolved decisions summary

| # | Decision | Resolution |
|---|---|---|
| 1 | Offline-first / local persistence | SwiftData, last-write-wins conflict resolution, backend as system of record |
| 2 | Push notifications | APNs direct integration, three types: PR achieved, workout reminder, show-up nudge |
| 3 | Product analytics | PostHog, defined V1 event set, anonymous IDs only |
| 4 | Onboarding flow | Seven screens max, goal selection + future self photo capture included, ends with first workout |
| 5 | Monetisation | Freemium, core logging free, AI features premium, all features unlocked for V1 launch period |
| 6 | Legal | User owns all data and assets, account deletion in V1, data export in V2, health disclaimer in onboarding |
| 7 | Deep linking | Universal Links from day one, domain registered before navigation code written |
| 8 | Backend language | Python + FastAPI, Supabase Python client |
| 9 | AI provider | Claude API for text, Fal.ai for image generation, both backend-only |
| 10 | Backup recovery | Supabase free tier during beta, Pro before public launch, restore tested during V1 development |

### Notifications — V1 event types

**PR achieved** — immediate, triggered by PR detection on WorkoutSet completion. Rich notification with PR details.

**Workout reminder** — user-configured schedule. Fires at user-set time on user-set days.

**Show-up nudge** — fires once on scheduled workout days if no session logged by user-configured nudge time. Tiny habits framing — minimum viable ask. Includes future self generated image as rich notification attachment.

### Onboarding flow — V1 sequence

Onboarding is split into two phases to minimize initial friction. Phase 1 collects only what's needed to log the first workout. Phase 2 is triggered after the first workout is completed, when the user has invested in the app and the context for the future self feature is clear.

**Phase 1 — Required (4 steps):**
```
Welcome → Sign in → Display name → Units → First workout prompt
```

**Phase 2 — Post-first-workout (progressive disclosure):**
```
Goal selection → Gender + DOB (skippable) →
BIPA consent + Photo capture (optional) →
[Fal.ai generates future self image in background] →
Future self reveal → Notification permission
```

Notification permission requested in Phase 2 — after the user has seen the future self image and understands the notification value proposition. This is the highest-context moment for the permission ask.

### Future self feature — V1

**Hard prerequisites (feature does not ship without these):**
- BIPA written consent obtained in Phase 2 onboarding, separate from general privacy policy
- DPA executed with Fal.ai before any photos are processed
- Photo deletion enforced: received by backend → forwarded to Fal.ai → deleted within 60 seconds → never written to disk → never logged — verified by automated test
- Quality gate: generate 2 variations via Fal.ai, score each using a second Claude API vision call on a 1–10 face similarity scale, present only the highest-scoring variation if score ≥ 6 — fallback message if no variation passes ("Your vision is being crafted — check back soon"). Quality score stored in AIRequestLog for trend analysis.
- Content warning displayed before image reveal
- Explicit opt-out available at any time from settings with immediate deletion of photo and generated images
- Framing is always "stronger and healthier" — never thinner, leaner, or weight-focused
- Images clearly labeled as AI-generated in app and in App Store review notes
- App Store review notes drafted and reviewed before submission

**Ongoing:**
- User photo + goal + gender sent to Fal.ai img2img pipeline via backend (never from iOS directly)
- Generated image stored in Supabase Storage private bucket — signed URLs only
- Generated image attached to show-up nudge notifications via APNs rich notifications
- User owns generated image. Company holds limited license to store and serve within app only
- Third party processors (Fal.ai) contractually prohibited from retaining or using photo data
- Manual regeneration available from settings. Automatic regeneration deferred to V2

### AI operations — async pattern

All AI operations (Claude API insights, Fal.ai image generation) are asynchronous in V1:

1. Client sends request → backend creates a Job record (`status: pending`), returns `job_id` immediately (HTTP 202)
2. Backend processes AI call via FastAPI BackgroundTasks (`status: processing`)
3. Client polls `GET /v1/jobs/{job_id}` with exponential backoff: 2s → 4s → 8s → 10s → 10s... (max 15 attempts, 10s ceiling)
4. On `complete` — client retrieves result from the job record
5. On `failed` — job record contains user-facing error message, client shows fallback
6. On `expired` (5-minute TTL exceeded) — a cleanup task sets status to `expired`, client shows fallback

**Job expiry:** A backend task runs every 60 seconds. Any job in `pending` or `processing` state with `expires_at < now()` is set to `expired` with a standard fallback message. This prevents hung jobs from being polled indefinitely.

**Client polling ceiling:** After 15 attempts (~2 minutes total with backoff), client stops polling and shows the `expired` fallback regardless of job status. This is a safety net for network edge cases.

**Wait state UX:** During polling the client shows progressive messaging, not a spinner. For future self generation: "Analyzing your photo…" (attempts 1–3) → "Building your future self…" (attempts 4–8) → "Almost ready…" (attempts 9–15). For insights: "Reviewing your session…" → "Generating your insight…". Time remaining estimate shown from attempt 3 onward. On quality gate failure: warm message — never technical error copy.

Redis + Celery deferred to V2 when job volume justifies the infrastructure overhead.

### AI cost controls

Per-user monthly AI spend limits enforced in V1:
- Future self image generation: max 5 regenerations per user per month
- AI workout insights: max 60 per user per month (2 per day average)
- Circuit breaker: if daily AI spend across all users exceeds a defined threshold, `ai_insights_enabled` flag is automatically disabled until manually re-enabled

**Revised cost estimate with quality gate overhead:**
Each future self generation makes 2 Fal.ai img2img calls + 1 Claude vision scoring call. This is approximately 2x–2.5x the cost of a naive single-generation approach. Updated estimate: $0.60–1.50/user/month for a user who uses all 5 regenerations, $0.10–0.25/user/month for a user who only uses AI insights. Blended estimate at V1 scale: ~$0.40–0.80/user/month. Revisit before V2 paywall decision with actual usage data.

**Quality gate failure behavior — fail-closed:**
If the Claude vision scoring call itself fails (network error, timeout, API error), the job returns the fallback message rather than showing the unscored image. Rationale: the future self image is an identity-adjacent emotional feature. Showing a poor result is a worse user experience than a thoughtful fallback. The scoring failure is logged in AIRequestLog with `quality_score: null`. A high null-score rate triggers a Sentry alert. This is a product decision — not a default technical behavior.

### Prompt versioning

AI prompts are stored in the database, not in code. Every AI response is tagged with the `prompt_version` used. This enables: prompt iteration without code deployment, A/B testing prompt variations, rollback of a bad prompt change, and historical comparison of insight quality.

```
PromptTemplate table:
id              uuid          primary key
feature         string        insight | future_self | benchmarking
version         string        v1.0, v1.1, etc
prompt_text     text
is_active       boolean       default false — only one active per feature
created_at      timestamp
```

### Monetisation — feature gating

**Free forever:** Unlimited workout logging, exercise library, workout history, PR detection, PR notifications, basic workout reminders.

**Premium:** AI workout insights, future self image generation and notifications, benchmarking and comparative statistics, progress charts and trend analysis, spreadsheet import (V2), body metrics tracking (V2).

All features unlocked for all users during V1 launch period. Paywall introduced at V2. Stripe integration at V4.

### Legal requirements

**Immediate actions (before any code is written):**
- USPTO trademark filing — intent-to-use application in Class 9 and Class 41. File this week. Every day without filing is a priority date risk. Do not wait for the app to be built.

**Before future self feature ships:**
- BIPA written consent flow reviewed by attorney
- Fal.ai DPA executed
- SCCs in place if Fal.ai processes outside EU/EEA
- Biometric consent version recorded in BiometricConsent table

**Before V1 public App Store launch:**
- Privacy Policy — explicitly covers photo data, AI-generated images, biometric processing, third party processors, EU user rights (GDPR Article 17 + 20 stopgap via "contact us" until V2 data export)
- Terms of Service — drafted and reviewed
- Health disclaimer — prominent in onboarding, not buried in terms
- AI content disclosure — generated images labeled in app, disclosed in App Store review notes
- Account deletion available, data deleted within 30 days
- Attorney review of Privacy Policy complete

**Ongoing commitments:**
- Data export — V2
- No user PII ever used for AI training
- No user data ever sold or used for advertising

---

## Development Workflow

### The Loop

Every component follows this sequence:

1. **Understand** — discuss the component here (Claude.ai chat) before any code is written. Concept first.
2. **Agree** — confirm approach and write acceptance criteria.
3. **Implement** — build component and tests together in Claude Code.
4. **Verify** — run tests, confirm green.
5. **Review** — walk through what was built and why.
6. **Close** — close the GitHub issue, update this document if any decisions were made.

### Ground Rules

- This document is the source of truth. Claude producing output that contradicts it is a signal to stop and reconcile.
- No code is written before the relevant Open Decision is resolved.
- No feature is marked Done without passing tests.
- No decision is changed without a Decision Log entry.

### CLAUDE.md

A `CLAUDE.md` file lives at the repo root. It contains the active summary of architectural decisions for Claude Code to read at the start of every session. When this document changes, `CLAUDE.md` is updated to match.

---

## Project Tracking

**Tool:** GitHub Projects (kanban within the same repo as the code)

**Columns:** Backlog → In Progress → In Review → Done

**Milestones:** V1, V2, V3, V4

**Labels:** `feature`, `bug`, `architecture`, `debt`, `security`, `testing`

**Issue template:**
```
## What
[One sentence description]

## Acceptance criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Tests required
- [ ] Test 1
- [ ] Test 2

## Phase
V1 / V2 / V3 / V4

## Open decisions resolved
[Any decisions from the Open Decisions table resolved by this issue]
```

---

## Decision Log

| # | Date | Decision | Rationale |
|---|---|---|---|
| 1 | April 2026 | iOS + iPadOS only for V1 | HealthKit and Watch advantages justify iOS-first. Android deferred to post-PMF. |
| 2 | April 2026 | SwiftUI over UIKit | Modern, declarative, iPadOS layout adaptations included. |
| 3 | April 2026 | Supabase for DB + Auth + Storage | Eliminates 3 separate V1 services. PostgreSQL with RLS. Generous free tier. |
| 4 | April 2026 | Railway for API hosting | Simplest deploy-on-push for solo V1. No DevOps overhead. |
| 5 | April 2026 | Monorepo on GitHub | Single issue tracker, CI config, and PR workflow for all layers. |
| 6 | April 2026 | Core Library as Swift Package | Enforces separation of business logic from UI. Fully unit testable without simulator. |
| 7 | April 2026 | ExerciseDB for exercise library | Large database with GIF demos. Best free option for V1. |
| 8 | April 2026 | PostHog for product analytics | Open source, privacy-respecting, self-host option available. |
| 9 | April 2026 | gender enum: male / female / na | Used as statistical input for benchmarking only. na is default, no feature gated on it. |
| 10 | April 2026 | measurement_unit as display preference | All measurements stored in cm. Conversion at display layer only. Prevents migration if user changes preference. |
| 11 | April 2026 | weight_modifier pattern for bodyweight exercises | Handles bodyweight / assisted / weighted variants as distinct records. Enables accurate PR tracking across variants. |
| 12 | April 2026 | secondary_muscle_groups as PostgreSQL array | Avoids junction table for compound movement secondary muscles. Native PostgreSQL array type supported by Supabase. |
| 13 | April 2026 | PersonalRecord is system-generated only | Triggered automatically on WorkoutSet completion. Users never create PR records directly. |
| 14 | April 2026 | previous_value stored on PersonalRecord | Denormalised for AI feedback performance. Avoids historical query on every PR notification. |
| 15 | April 2026 | Structured JSON logging from day one | Retrofitting structure into unstructured logs is painful. Aggregation platform deferred to V2, structure is not. |
| 16 | April 2026 | Staging + production environments on Railway | No direct pushes to production. Manual promotion from staging. |
| 17 | April 2026 | SwiftData for local persistence, last-write-wins conflict resolution | Offline-first is non-negotiable for gym use. Backend is system of record. Last-write-wins covers 99% of fitness data conflict scenarios. |
| 18 | April 2026 | APNs direct integration, three V1 notification types | PR achieved, workout reminder, show-up nudge. Permission requested after onboarding not on launch. OneSignal deferred to V2. |
| 19 | April 2026 | PostHog V1 event set defined | Instruments onboarding, workout logging, engagement, and retention signals. Anonymous IDs only — no PII in events. |
| 20 | April 2026 | Onboarding flow — seven screens max | Includes goal selection and future self photo capture. Ends with first workout prompt. Notification permission at end of onboarding. |
| 21 | April 2026 | Future self AI image generation in V1 | Fal.ai img2img pipeline. User owns generated image. Private storage only. Rich notification attachment on show-up nudge. Manual regeneration in settings. |
| 22 | April 2026 | Freemium monetisation, all features unlocked for V1 launch | Core logging free forever. AI features premium. Paywall at V2. Stripe at V4. Launch period unlock gets clean usage data before paywall. |
| 23 | April 2026 | Strong user data ownership position | User owns all data and generated assets. No PII used for AI training. No data sold. Account deletion in V1. Privacy policy covers photo and AI image data explicitly. |
| 24 | April 2026 | Universal Links from day one | Domain registered before navigation code written. Retrofit from URL schemes is painful. |
| 25 | April 2026 | Python + FastAPI backend | Consistent with QA automation background in Python. Natural fit for AI integration work. FastAPI auto-docs serve as iOS ↔ backend contract reference. |
| 26 | April 2026 | Claude API for text AI, Fal.ai for image AI | Claude for reasoning quality on insights and benchmarking. Fal.ai for face-consistent future self generation. Both accessed through backend only — keys never in iOS app. |
| 27 | April 2026 | Supabase Pro before public App Store launch | Free tier 24hr recovery acceptable during beta. Pro 7-day window required before real user data at risk. Restore process tested once during V1 development. |
| 28 | April 2026 | SyncEventLog entity for offline-first debugging | Offline sync failures are undiagnosable without device-side visibility. Local SwiftData table uploadable on failure or on demand via problem reporter. |
| 29 | April 2026 | In-app SupportReport with anonymous user ID capture | PII-free logs mean email cannot be used to find logs. Problem reporter captures anonymous ID for correlation. Admin Supabase query maps email to ID when user contacts support directly. |
| 30 | April 2026 | AIRequestLog in separate access-controlled Supabase table | AI quality issues undiagnosable without prompt and response history. Separate table prevents AI data bleeding into general observability tooling. 30-day retention, admin access only. |
| 31 | April 2026 | SwiftData migration version flags in UserDefaults | Failed migrations can corrupt local data silently. Version flags before and after every migration enable detection and recovery flow on next launch. |
| 32 | April 2026 | 90% test coverage target enforced by CI | Aspirational coverage targets degrade silently. Hard CI gate on both iOS and backend pipelines prevents regression. |
| 33 | April 2026 | Protocol-based dependency injection as iOS mocking strategy | Avoids third party mocking frameworks. Swift Testing handles test doubles natively. Every external dependency injected as a protocol. |
| 34 | April 2026 | pytest-mock + httpx mock transport for backend mocking | pytest-mock for unit-level mocking. httpx mock transport for HTTP-level external API mocking. Keeps tests fast, deterministic, and free of external dependencies. |
| 35 | April 2026 | TestFlight internal + external tiers configured from V1 | Internal (25 people, automatic) for close collaborators. External (10,000, manual promote) for broader beta. Same binary, feature access controlled by flags. |
| 36 | April 2026 | PostHog feature flags for beta access control and progressive rollout | Already using PostHog for analytics — no additional tool needed. Flags togglable per user or cohort without code changes or new builds. |
| 37 | April 2026 | Three V1 feature flags defined | `premium_features_enabled`, `future_self_enabled`, `ai_insights_enabled`. Allows independent cost and access control during beta. |
| 38 | April 2026 | beta_tier field on User as database-level access override | Two-layer access control — PostHog flags checked first, beta_tier as fallback guarantee. Decouples access control from PostHog availability. |
| 39 | April 2026 | App name: PRLifts | PR = Personal Record — core motivational hook. Lifts = plural, every session, gym-native language. Domain confirmed available: prlifts.app (primary, Universal Links), prlifts.com (defensive). USPTO trademark clearance search required before filing in Class 9 and Class 41. |
| 40 | April 2026 | `goal` field added to User entity | Collected in Phase 2 onboarding. Drives future self image generation prompt. Nullable — not required for core app use. |
| 41 | April 2026 | Two-phase onboarding | Phase 1 (4 steps) gets user to first workout. Phase 2 (post-first-workout) introduces future self feature with BIPA consent. Reduces onboarding drop-off and provides better consent context. |
| 42 | April 2026 | AI operations are asynchronous (FastAPI BackgroundTasks) | Synchronous AI calls in request/response cycle will timeout (Fal.ai 10-30s, Claude 2-5s). BackgroundTasks + status polling in V1. Redis + Celery deferred to V2. |
| 43 | April 2026 | Server-assigned timestamps for conflict resolution | Client clocks drift and can be manipulated. `server_received_at` governs last-write-wins resolution. Client sends `client_created_at` for context only. |
| 44 | April 2026 | OpenAPI spec committed to repo as contract | Auto-generated from FastAPI on every CI build. Drift without version bump fails CI. The committed spec is the iOS ↔ backend contract — not the live docs endpoint. |
| 45 | April 2026 | Future self feature has hard prerequisites before shipping | BIPA written consent, Fal.ai DPA, photo deletion within 60s enforced and tested, quality gate with graceful fallback, content warning, opt-out with immediate deletion, "stronger and healthier" framing only. |
| 46 | April 2026 | SSL certificate pinning on iOS (TrustKit) | Gym WiFi is an adversarial network. Certificate pinning on backend connection prevents MITM attacks on photo upload and auth flows. |
| 47 | April 2026 | Concrete rate limits defined per endpoint | AI: 10 req/min/user. Auth: 5 attempts/min/IP. Workout log: 100 req/min/user. Enforced via FastAPI middleware + Redis. |
| 48 | April 2026 | Prompt versioning — prompts stored in PromptTemplate table | Enables prompt iteration without code deploy, A/B testing, rollback, and historical quality comparison. PromptTemplate is a V1 entity. |
| 49 | April 2026 | AI cost controls defined | Future self: 5 regenerations/user/month. Insights: 60/user/month. Daily spend circuit breaker auto-disables ai_insights_enabled flag. |
| 50 | April 2026 | Accessibility as V1 requirement | VoiceOver labels, Dynamic Type, 44pt touch targets on all interactive elements. App Store compliance requires it. Tested in CI via XCTest accessibility audits. |
| 51 | April 2026 | Alerting thresholds defined before launch | Error rate, CPU, connection pool, AI latency, daily AI spend, iOS crash-free rate — all configured in Sentry and Railway before public launch. |
| 52 | April 2026 | Runbook written before launch | Covers Railway rollback, Supabase restore, API key rotation, feature flag emergency disable. |
| 53 | April 2026 | Secret management via Railway env vars | No secrets in code or repo. Rotation procedure documented per secret. Pre-launch secrets audit before first public build. |
| 54 | April 2026 | Railway always-on before public launch | Cold starts during onboarding AI flow are unacceptable UX. Always-on enabled on Railway paid plan before launch. |
| 55 | April 2026 | muscle_group, category, equipment flagged for V2 lookup table migration | PostgreSQL enums are painful to extend. Stable enums remain (status, weight_modifier, etc). High-change enums migrate to lookup tables in V2. |
| 56 | April 2026 | Database indexes defined in initial migration | idx_workout_user_started, idx_pr_user_exercise, idx_exercise_name, idx_workout_exercise_order, idx_workout_set_order, idx_ai_log_expires, idx_sync_log_upload — all in initial migration. |
| 57 | April 2026 | Photo deletion policy: within 60 seconds, verified by automated test | Photo never written to disk, never logged. Deleted from all systems within 60s of image generation. Automated test verifies deletion. |
| 58 | April 2026 | BiometricConsent as a separate table | Legal audit record of biometric consent. Server-assigned timestamp. Includes consent version and policy text hash. Required before future_self_enabled flag activates per user. Separate table supports versioned re-consent on policy changes. |
| 59 | April 2026 | Job table for async AI operations | Tracks all async AI jobs. 5-minute TTL via expires_at. Cleanup task runs every 60 seconds. Client exponential backoff: 2s initial, 10s ceiling, 15 attempt maximum. Defined fallback on expired/failed. |
| 60 | April 2026 | Upstash Redis for rate limiting | Redis required for FastAPI rate limiting middleware. Upstash chosen for Railway compatibility and free tier adequacy for V1. Connection string stored as Railway env var. |
| 61 | April 2026 | TrustKit pinning at CA level with backup pin | Leaf pinning causes self-imposed outages on certificate rotation. CA pinning with backup pin + rotation procedure in runbook eliminates the risk. |
| 62 | April 2026 | prompt_template_id foreign key on AIRequestLog | Enables historical quality comparison across prompt versions. Core to making prompt versioning meaningful — without this the AIRequestLog and PromptTemplate are disconnected. |
| 63 | April 2026 | PR detection index on WorkoutSet | idx_workout_set_pr_detection covers the per-set-completion PR query. Without it, PR detection scales as O(n) full scan of all user sets. |
| 64 | April 2026 | Quality gate: Claude vision scoring, threshold 6/10 | Concrete and testable quality gate. Two Fal.ai variations scored by Claude vision. Score >= 6 passes. Score stored in AIRequestLog for trend analysis. |
| 65 | April 2026 | Background sync trigger points defined | NWPathMonitor for connectivity restore. scenePhase .active for app foreground. BGAppRefreshTask for background. SyncEventLog force-quit recovery on next launch. |
| 66 | April 2026 | Photo deletion test moved to automated CI suite | Pre-launch checklist items get written once. Security tests tagged @security run on every push. Photo deletion is a security requirement — it must be in CI not just a checklist. |
| 67 | April 2026 | Polling wait state UX defined | Progressive messaging during job polling. Time estimate from attempt 3. Clear fallback copy on quality gate failure and job expiry. Never blank screen or technical error copy. |
| 68 | April 2026 | USPTO trademark filing as immediate action | Filing intent-to-use this week establishes priority date. Deferring to pre-launch puts the name at risk. File now, before building. |
| 69 | April 2026 | APScheduler (AsyncIOScheduler) for backend scheduled tasks | FastAPI BackgroundTasks cannot run periodic tasks. APScheduler runs in-process on FastAPI startup — no additional infrastructure. Celery Beat deferred to V2 with rest of Celery. Job cleanup runs every 60 seconds. |
| 70 | April 2026 | Quality gate fail-closed on scoring failure | If Claude vision scoring call fails, return fallback message rather than unscored image. Future self is identity-adjacent — a poor result is worse UX than a thoughtful fallback. Scoring failure logged with quality_score: null. High null rate triggers Sentry alert. |
| 71 | April 2026 | AI cost estimate revised with quality gate overhead | Two Fal.ai calls + one Claude vision call per generation = 2x–2.5x original estimate. Blended estimate revised to $0.40–0.80/user/month. Revisit before V2 paywall with actual data. |
| 72 | April 2026 | BiometricConsent RLS: read user_id = auth.uid(), writes backend-only | User cannot tamper with consent audit record from client. Service role key required for writes. This is the legal integrity of the BIPA compliance posture. |
| 73 | April 2026 | BGAppRefreshTask is opportunistic, not a primary sync trigger | Background refresh can be disabled by user in iOS Settings. Primary triggers are app foreground and NWPathMonitor. BGAppRefreshTask is registered as best-effort only. Architecture never assumes it fires. |
| 74 | April 2026 | idx_job_user_type_month index for cost control queries | Monthly usage count check before each AI job would be a full scan without this index. Covers user_id + job_type + created_at DESC for efficient monthly count. |
| 76 | April 2026 | EDB (ExerciseDB v2 by ASCEND API) chosen over ExerciseDB v1 for seed data | Same creator as v1, same field structure, 11,000+ exercises vs 1,300, includes videos/GIFs/images. Switched before any code written — zero migration cost. V1 on RapidAPI remains available as fallback. |
