# PRLifts — Claude Code Briefing

> This file is read at the start of every Claude Code session.
> Full detail lives in ARCHITECTURE.md. When in doubt, ARCHITECTURE.md wins.
> Never produce output that contradicts ARCHITECTURE.md without flagging the conflict first.

---

## What this project is

PRLifts is an iOS + iPadOS fitness tracking app. Two differentiators:
1. **AI feedback layer** — PR detection, volume trends, benchmarking, workout insights via Claude API
2. **Future self vision board** — AI-generated image of the user looking fit, anchors motivational show-up nudge notifications

Current phase: **V1 — MVP**

---

## Repo structure

```
prlifts/
  ios-app/          SwiftUI app — thin UI layer only
  core-library/     Swift Package — all business logic
  backend/          Python + FastAPI — REST API + AI services
  docs/             ARCHITECTURE.md and supporting docs
```

---

## Architecture rules — never violate these

1. **SwiftUI → Core Library → Backend. Never skip a layer.**
   - iOS app never calls the backend directly
   - iOS app never calls external APIs directly (Claude, Fal.ai, ExerciseDB)
   - Core Library has zero knowledge of SwiftUI or UIKit
   - All AI API keys live on the backend only — never in the iOS app

2. **Business logic lives in the Core Library, not the iOS app.**
   PR detection, workout calculations, data parsing, AI service interfaces — all Core Library.

3. **Backend is platform-agnostic.**
   Design every endpoint as if Android and web clients will also consume it.

4. **Dependency injection throughout.**
   Every external dependency is a protocol (Swift) or abstract interface (Python).
   Production code receives real implementations. Test code receives mocks.

5. **Nothing is Done without tests.**
   Tests ship in the same PR as the feature. 90% coverage enforced by CI.
   Acceptance criteria are written before implementation begins.

6. **Structured JSON logging on every backend request.**
   Shape: user_id, endpoint, duration_ms, status_code, error_code

7. **All AI operations are asynchronous.**
   No AI call runs synchronously in a request/response cycle.
   Pattern: client sends request, backend returns job_id (HTTP 202), client polls status endpoint, result retrieved on completion.

8. **Conflict resolution uses server timestamps.**
   server_received_at governs last-write-wins. Client client_created_at is context only.

9. **OpenAPI spec is the iOS/backend contract.**
   openapi.json is committed to the repo, generated on every CI build. Spec drift without a version bump fails CI.

10. **Photo data is never written to disk or logged.**
    User photo: received, forwarded to Fal.ai, deleted within 60 seconds. No exceptions.

---

## Tech stack — quick reference

| Layer | Technology |
|---|---|
| iOS UI | SwiftUI |
| Local persistence | SwiftData (offline-first, server-timestamp conflict resolution) |
| iOS dependency mgmt | Swift Package Manager |
| iOS testing | XCTest + Swift Testing + XCUITest |
| iOS security | TrustKit SSL certificate pinning on backend connection |
| Core Library | Swift Package — no UIKit, no SwiftUI |
| Backend language | Python |
| Backend framework | FastAPI |
| Backend async | FastAPI BackgroundTasks (V1), Redis + Celery (V2) |
| Backend testing | pytest + pytest-mock + pytest-cov + httpx |
| Database | PostgreSQL via Supabase |
| Auth | Supabase Auth (Sign in with Apple, Google, email) |
| Storage | Supabase Storage (private buckets) |
| Backend hosting | Railway (staging + production, always-on before public launch) |
| Rate limiting | FastAPI middleware + Redis |
| Text AI | Anthropic Claude API — backend only |
| Image AI | Fal.ai img2img — backend only |
| Prompt storage | PromptTemplate table in Supabase — not in code |
| Exercise library | ExerciseDB via RapidAPI |
| Crash reporting | Sentry (iOS + backend) |
| Product analytics | PostHog (feature flags + events) |
| CI — iOS | Xcode Cloud |
| CI — backend | GitHub Actions |
| Source control | GitHub monorepo |

---

## Testing requirements

- **Coverage target: 90%** on Core Library and backend business logic — enforced by CI
- **Unit tests** cover all Core Library logic — runnable without simulator
- **XCUITest** covers critical flows only: login, log workout, view history, PR notification
- **Accessibility tests** — VoiceOver, Dynamic Type, 44pt touch targets — required for V1
- **pytest** covers all backend business logic and API endpoints
- **Offline sync test matrix** — 5 scenarios must have explicit integration tests (see ARCHITECTURE.md)
- **AI feature test cases** — 5 boundary conditions must be tested including graceful degradation (see ARCHITECTURE.md)
- **Mocking strategy:**
  - iOS: protocol-based injection + Swift Testing test doubles — no third party mocking frameworks
  - Backend: pytest-mock for unit mocks, httpx mock transport for external HTTP APIs
- **CI gates:**
  - Xcode Cloud blocks TestFlight distribution on test failure or coverage below 90%
  - GitHub Actions blocks PR merge on test failure or coverage below 90%

---

## Security rules

- Auth tokens stored in iOS Keychain — never UserDefaults
- SSL certificate pinning on iOS (TrustKit) — gym WiFi is adversarial
- Row Level Security enforced on all Supabase tables — user_id = auth.uid()
- No PII in logs or Sentry — anonymous user IDs only
- Rate limits: AI 10 req/min/user, Auth 5 attempts/min/IP, Workout log 100 req/min/user
- Rate limiting enforced via FastAPI middleware + Redis
- Strict input validation on every inbound payload
- All endpoints versioned under /v1/
- Photo data: received, forwarded, deleted within 60s — never written to disk

---

## Data model — entity summary

| Entity | Phase | Notes |
|---|---|---|
| User | V1 | Includes goal enum + beta_tier enum for feature access control |
| Exercise | V1 | Primary + secondary muscle groups, ExerciseDB or user-created |
| Workout | V1 | Status: in_progress / paused / partial_completion / completed |
| WorkoutExercise | V1 | Junction — ordered exercises within a workout |
| WorkoutSet | V1 | weight_modifier handles bodyweight / assisted / weighted variants |
| PersonalRecord | V1 | System-generated only, never user-created |
| SyncEventLog | V1 | Device-side offline sync debugging — uploadable on demand |
| SupportReport | V1 | In-app problem reporter — captures anonymous user ID for log correlation |
| AIRequestLog | V1 | Access-controlled table — AI prompt + response, 30-day retention |
| PromptTemplate | V1 | AI prompts stored in DB not code — versioned, one active per feature |
| WorkoutPlan | V2 | Structured programs |
| WorkoutPlanDay | V2 | Days within a plan |
| WorkoutPlanExercise | V2 | Prescribed exercises per plan day |
| BodyMetrics | V2 | All measurements stored in cm regardless of display preference |
| StepsEntry | V2 | Daily aggregate — one row per user per date |

Key data rules:
- All measurements stored in cm — convert at display layer only
- weight_unit stored per WorkoutSet — never rely solely on User preference
- PersonalRecord tracks weight_modifier — weighted and bodyweight PRs are separate records
- AI prompt/response logs are in a separate table, admin access only
- goal on User is nullable — collected in Phase 2 onboarding, not required for core app
- Database indexes are defined in the initial migration — do not add features without checking index coverage

---

## Feature flags (PostHog)

| Flag | Controls |
|---|---|
| premium_features_enabled | Full premium access |
| future_self_enabled | AI image generation (per-call cost — has hard legal prerequisites before enabling) |
| ai_insights_enabled | AI workout feedback (circuit breaker auto-disables if daily spend threshold hit) |

Access control is two-layer: PostHog flag checked first, beta_tier on User as fallback.

---

## Notifications — V1 types

| Type | Trigger | Notes |
|---|---|---|
| PR achieved | WorkoutSet completion, PR detected | Rich notification, immediate |
| Workout reminder | User-configured schedule | Fires at user-set time |
| Show-up nudge | Scheduled workout day, no session logged by nudge time | Fires once, tiny habits framing, future self image attached |

All notifications via APNs direct integration. Universal Links configured for all notification deep links.

---

## Onboarding flow — two phases

Phase 1 — Required (4 steps, before first workout):
Welcome, Sign in, Display name, Units, First workout prompt

Phase 2 — Post-first-workout (progressive disclosure):
Goal selection, Gender + DOB (skippable), BIPA consent + Photo capture (optional),
Fal.ai generates future self image (async, quality-gated), Future self reveal, Notification permission

Future self feature has hard legal prerequisites before future_self_enabled flag can be turned on. See ARCHITECTURE.md Security — Biometric Data section.

---

## AI operations pattern

All AI calls are async. Never call Claude or Fal.ai synchronously in a request handler.

POST /v1/jobs/insights     returns job_id (HTTP 202)
GET  /v1/jobs/{job_id}     returns status: pending|processing|complete|failed, result if complete

Prompt templates are fetched from the PromptTemplate table — never hardcoded.

---

## Project management — how work is structured

Full details in docs/PROJECT_MANAGEMENT.md. Summary for every session:

**Sprint model:** One-week Scrum sprints. Potentially shippable increment every Friday.

**Your team:** Backend, iOS, Infrastructure, or UX/Design. Every story belongs to one team.

**Your workflow every session:**
1. Read CLAUDE.md (this file) — full briefing, no skipping
2. Read the assigned GitHub Issue — acceptance criteria, technical notes, dependencies
3. Read any linked docs sections before writing code
4. Work on ONE story — never combine stories in one session
5. Write tests alongside implementation — never after
6. Open a PR when done — human reviews and merges, you do not merge your own PRs

**Definition of Done — every story:**
- All acceptance criteria satisfied
- Tests written and passing at 90% coverage
- No linting violations (SwiftLint / Ruff): both `ruff check .` and `ruff format --check .` must pass in `backend/`
- No mypy errors
- **iOS PRs: run Cmd+B in Xcode and confirm 0 errors, 0 warnings before opening the PR. A build failure is a blocking PR issue. Run UI tests on the iPhone SE (3rd generation) simulator before pushing — UDID `6C107B89-D600-4A9E-81BA-3606168CD8A3`. It is the minimum supported screen size and catches layout and touch target regressions that wider devices miss.**
- PR opened with clear description
- ARCHITECTURE.md updated if any decision was made

**What you never do independently:**
- Make product decisions — flag and ask
- Make visual design decisions without an approved Claude Design handoff bundle
- Merge your own PRs
- Activate prompt templates
- Add new dependencies without flagging
- Work on V2+ features — flag if you see one referenced

**Design handoffs:**
UI stories come with a Claude Design handoff bundle linked in the GitHub Issue.
The bundle contains the approved prototype, design intent, and component specs.
Read the bundle before writing any SwiftUI code. The bundle is the spec —
SCREEN_INVENTORY.md and USER_FLOWS.md are reference documents, the bundle is
what you build against.

**Labels that affect your work:**
- `security` — complete security review checklist before marking Done
- `legal-blocked` — do not start, prerequisite must be resolved first
- `design-required` — do not start iOS UI work without approved spec
- `ai-ml` — prompt evaluation suite must pass before activation

---

## One-time repo setup (after cloning)

Run this once to wire the tracked git hooks:

```bash
bash backend/scripts/install_hooks.sh
```

This sets `core.hooksPath = .githooks` so the pre-commit hook in `.githooks/`
runs on every commit. The hook runs:
- `xcodebuild test` (PRLifts scheme, iPhone SE simulator) when any `.swift` file is staged — runs PRLiftsTests + PRLiftsUITests and blocks the commit if any test fails
- `ruff check .` and `ruff format --check .` on the backend — blocks the commit if either fails

**Never use `git commit --no-verify`.** The pre-commit hook is mandatory. If the hook fails, fix the underlying issue — do not bypass it. UI tests are excluded from the Xcode Cloud PR CI gate (see ARCHITECTURE.md Decision 91); the pre-commit hook is the only hard gate on UI tests before a PR is opened.

---

## Development workflow — the loop

Every task follows this sequence before closing the GitHub issue:

1. Understand the component (discuss in Claude.ai chat first)
2. Confirm approach + write acceptance criteria
3. Implement component + tests together
4. Run tests — confirm green
5. Confirm coverage >= 90%
6. Review what was built
7. Update ARCHITECTURE.md if any new decisions were made
8. Close GitHub issue

Ground rules:
- No code written before acceptance criteria exist
- No feature marked Done without passing tests at 90% coverage
- No architectural decision changed without a Decision Log entry in ARCHITECTURE.md
- When this file conflicts with ARCHITECTURE.md, ARCHITECTURE.md wins
- Flag conflicts rather than resolve them silently

---

## What phase are we in?

V1. If a feature, entity, or dependency is marked V2 or later in ARCHITECTURE.md, do not implement it. Flag it and ask.

---

## Pre-launch checklist (before public App Store release)

- [ ] BIPA written consent flow implemented and reviewed by attorney
- [ ] Fal.ai DPA executed
- [ ] Photo deletion automated test passing (60-second window)
- [ ] SSL certificate pinning verified on iOS
- [ ] Rate limiting configured and tested
- [ ] Railway always-on enabled
- [ ] Supabase Pro active (7-day recovery window)
- [ ] Backup restore tested
- [ ] Alerting thresholds configured in Sentry + Railway
- [ ] Runbook written and tested
- [ ] Secrets audit — nothing in git history or hardcoded
- [ ] OpenAPI spec committed and CI drift check passing
- [ ] Accessibility audit passing (VoiceOver, Dynamic Type)
- [ ] App Store review notes drafted for future self feature
- [ ] Privacy Policy reviewed by attorney
- [ ] USPTO trademark filing submitted (Class 9 + Class 41)
