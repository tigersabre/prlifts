# PRLifts — Regression Test Suite Map

**Version:** 1.0
**Last updated:** April 2026
**Owner:** QA Lead
**Audience:** All developers (human and Claude Code)

> When a feature changes, this map tells you exactly which tests
> to run and which existing tests might break.
> Organised by feature area, not by test file.

---

## How to Use This Document

1. Identify what changed (feature area in left column)
2. Find all affected test areas (right column)
3. Run all affected tests before opening a PR
4. If any test you expected to pass now fails: understand why before proceeding

---

## Feature → Test Coverage Map

### Workout Set Logging

**When changed, run:**
- `tests/services/test_workout_service.py` — core set logging logic
- `tests/services/test_pr_detection_service.py` — PR detection triggered on set completion
- `tests/routes/test_workout_sets.py` — endpoint contract
- `tests/security/test_input_validation.py::test_workout_set_input_validation` — bounds checking
- `tests/security/test_auth_boundaries.py` — ownership verification
- iOS: `WorkoutSetRowViewModelTests` — display formatting
- iOS: `PRDetectionTests` — client-side PR handling

**These tests will break if the WorkoutSet schema changes:**
- `tests/fixtures/test_fixtures.py` — stub factories
- `tests/services/test_pr_detection_service.py` — uses WorkoutSet directly
- Any test that calls `make_workout_set()`

---

### PR Detection

**When changed, run:**
- `tests/services/test_pr_detection_service.py` — all PR detection scenarios
- `tests/services/test_workout_service.py` — PR detection integration
- `tests/routes/test_workout_sets.py` — is_personal_record in response
- iOS: `PRDetectionTests` — client PR detection display
- iOS: `PRNotificationBannerTests` — banner trigger conditions

**Critical test cases for PR detection:**
- Weighted vs bodyweight variants tracked separately
- RPE-based PRs (lower RPE at same weight)
- First-ever set always creates a PR
- Incomplete sets do not trigger PR detection

---

### AI Workout Insights (Job Flow)

**When changed, run:**
- `tests/services/test_ai_service.py` — insight generation
- `tests/services/test_job_service.py` — job lifecycle
- `tests/routes/test_jobs.py` — job creation and polling endpoints
- `tests/background/test_job_cleanup.py` — APScheduler cleanup task
- `tests/security/test_rate_limiting.py` — monthly limit enforcement
- iOS: `JobPollingTests` — exponential backoff and polling behaviour

---

### Future Self Image Generation

**When changed, run:**
- `tests/services/test_future_self_service.py` — image generation flow
- `tests/services/test_quality_gate_service.py` — scoring and fail-closed behaviour
- `tests/security/test_photo_deletion.py` — photo deletion within 60s (@security)
- `tests/security/test_biometric_consent.py` — consent enforcement (@security)
- `tests/routes/test_jobs.py` — future_self job creation endpoint
- iOS: `FutureSelfRevealTests` — progressive messaging and fallback states

---

### Phase 2 Onboarding

**When changed, run:**
- iOS: `OnboardingFlowTests` — full Phase 2 happy path
- iOS: `BiometricConsentScreenTests` — consent UI
- iOS: `PhotoCaptureScreenTests` — photo submission
- iOS: `FutureSelfRevealTests` — reveal flow and polling
- iOS: `NotificationPermissionTests` — permission request timing
- `tests/security/test_biometric_consent.py` — backend consent enforcement

---

### Authentication

**When changed, run:**
- `tests/security/test_auth_boundaries.py` — full auth boundary suite
- `tests/routes/test_users.py` — user profile endpoints
- iOS: `AuthTests` — sign-in flows, token storage

---

### Push Notifications

**When changed, run:**
- `tests/background/test_notification_jobs.py` — send_workout_reminders, send_show_up_nudges
- iOS: `DeepLinkTests` — notification tap → deep link → correct screen
- iOS: `NotificationHandlerTests` — foreground vs background notification handling

---

### Sync and Offline

**When changed, run:**
- iOS: `SyncTests` — all offline sync scenarios (see test matrix below)
- iOS: `SyncEventLogTests` — event logging and upload
- `tests/routes/test_workouts.py` — upsert idempotency
- `tests/routes/test_workout_sets.py` — upsert idempotency

**Sync test matrix (must all pass):**

| Scenario | Test name |
|---|---|
| Successful sync after offline | `test_pendingSet_syncsSuccessfully_whenConnectivityRestored` |
| Multiple offline sets sync in order | `test_multipleOfflineSets_syncInCreationOrder` |
| Sync during active workout | `test_sync_doesNotInterrupt_activeWorkoutLogging` |
| Force-quit recovery | `test_forcequitRecovery_requeuesUnsyncedEntries_onNextLaunch` |
| Conflict resolution (last-write-wins) | `test_conflictResolution_usesServerTimestamp_notClientTimestamp` |

---

### Database Schema Changes

**When any schema changes, run everything:**
- Full backend test suite: `pytest --cov=app`
- Full iOS test suite: `xcodebuild test`
- Verify migrations apply cleanly to staging database
- Verify seed data still runs successfully

---

### Prompt Templates

**When prompt text changes, run:**
- `tests/prompt_evaluation/` — full evaluation suite (blocking for body image prompt)
- `tests/services/test_ai_service.py` — response validation
- Manual review against AI_RESPONSE_EXAMPLES.md

---

### Environment Configuration

**When ENV_CONFIG.md changes, run:**
- `tests/test_config.py` — verifies required variables are present
- Deploy to staging and run health check before production

---

## Running Targeted Tests

```bash
# Run a specific feature area
pytest tests/services/test_pr_detection_service.py -v

# Run all security tests
pytest -m security -v

# Run all tests except slow integration tests
pytest -m "not integration" -v

# Run the sync test matrix
pytest -k "sync" -v

# Run everything (pre-PR gate)
pytest --cov=app --cov-fail-under=90
```

```bash
# iOS — run specific test class
xcodebuild test \
  -scheme PRLifts \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  -only-testing:PRLiftsTests/PRDetectionTests

# iOS — run all tests
xcodebuild test \
  -scheme PRLifts \
  -destination 'platform=iOS Simulator,name=iPhone 16'
```

