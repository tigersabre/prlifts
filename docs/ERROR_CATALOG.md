# PRLifts — Error Catalog

**Version:** 1.0
**Last updated:** April 2026
**Owners:** Backend Platform Lead + iOS Platform Lead
**Audience:** All developers (human and Claude Code)

> Every error code in the system is defined here. This is the single source
> of truth for error codes, HTTP status mappings, and user-facing messages.
> If you need a new error code, add it here first. Never invent error codes
> in implementation code without adding them to this catalog.

---

## Error Response Format

Every error response from the backend follows this structure:

```json
{
  "error_code": "workout_not_found",
  "message": "This workout could not be found.",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

- `error_code` — machine-readable, snake_case, used by iOS to determine behaviour
- `message` — human-readable, safe to display to users, never contains internal detail
- `request_id` — the correlation_id for this request, used for support queries

---

## Error Code Convention

Format: `{domain}_{specific_error}`

Domains:
- `auth_` — authentication and authorisation errors
- `workout_` — workout and set logging errors
- `exercise_` — exercise library errors
- `job_` — async job errors
- `ai_` — AI provider errors
- `sync_` — sync and data errors
- `user_` — user profile errors
- `rate_` — rate limiting errors
- `biometric_` — biometric consent errors
- `system_` — unexpected system errors

---

## Auth Errors

| Error code | HTTP status | User-facing message | Notes |
|---|---|---|---|
| `auth_token_invalid` | 401 | "Your session has expired. Please sign in again." | JWT validation failed |
| `auth_token_expired` | 401 | "Your session has expired. Please sign in again." | JWT past expiry |
| `auth_token_missing` | 401 | "Authentication required." | No token in request |
| `auth_provider_failure` | 502 | "Sign in is temporarily unavailable. Please try again." | Apple/Google auth error |
| `auth_account_not_found` | 404 | "No account found. Please create an account first." | Token valid but no user record |
| `auth_account_deleted` | 410 | "This account has been deleted." | Deleted account token used |
| `auth_insufficient_permissions` | 403 | "You don't have permission to do that." | Valid token, wrong role |

---

## Workout Errors

| Error code | HTTP status | User-facing message | Notes |
|---|---|---|---|
| `workout_not_found` | 404 | "This workout could not be found." | Workout ID not in DB or wrong user |
| `workout_not_owned` | 403 | "You don't have access to this workout." | RLS violation attempt |
| `workout_already_completed` | 409 | "This workout is already completed." | Attempt to add to completed workout |
| `workout_exercise_not_found` | 404 | "This exercise entry could not be found." | WorkoutExercise not found |
| `workout_set_invalid` | 422 | "The set data is invalid. Please check your entries." | Validation failure — no reps, weight, or duration |
| `workout_set_not_found` | 404 | "This set could not be found." | WorkoutSet not found |

---

## Exercise Errors

| Error code | HTTP status | User-facing message | Notes |
|---|---|---|---|
| `exercise_not_found` | 404 | "This exercise could not be found." | Exercise ID not found |
| `exercise_name_taken` | 409 | "An exercise with this name already exists." | Duplicate custom exercise name |
| `exercise_not_editable` | 403 | "This exercise cannot be edited." | Attempt to edit ExerciseDB exercise |
| `exercise_in_use` | 409 | "This exercise is used in existing workouts and cannot be deleted." | Delete attempt on referenced exercise |

---

## Job Errors

| Error code | HTTP status | User-facing message | Notes |
|---|---|---|---|
| `job_not_found` | 404 | "This job could not be found." | Job ID not found or wrong user |
| `job_expired` | 410 | "This request took too long. Please try again." | Job TTL exceeded |
| `job_already_complete` | 409 | "This job is already complete." | Duplicate completion attempt |
| `job_monthly_limit_reached` | 429 | "You've used all your image generations for this month. Come back next month." | future_self job type limit (5/month) |
| `job_insight_limit_reached` | 429 | "You've reached your daily insight limit. Come back tomorrow." | insight job type limit (60/month) |

---

## AI Errors

| Error code | HTTP status | User-facing message | Notes |
|---|---|---|---|
| `ai_provider_unavailable` | 503 | "This feature is temporarily unavailable. Please try again later." | Claude or Fal.ai returned an error |
| `ai_provider_timeout` | 504 | "This took longer than expected. Please try again." | Provider exceeded timeout |
| `ai_quality_gate_failed` | 200* | "Your vision is being crafted — check back soon." | *Returns 200 with failed job status |
| `ai_response_invalid` | 500 | "Something went wrong generating your insight. Please try again." | Response failed validation |
| `ai_scoring_failed` | 200* | "Your vision is being crafted — check back soon." | *Fail-closed — same as quality gate |
| `ai_disabled` | 503 | "AI features are temporarily disabled. We'll be back soon." | Circuit breaker active |

---

## Sync Errors

| Error code | HTTP status | User-facing message | Notes |
|---|---|---|---|
| `sync_conflict` | 409 | None — handled silently | Last-write-wins, server timestamp |
| `sync_entity_not_found` | 404 | None — handled silently | Entity deleted on server since last sync |
| `sync_validation_failed` | 422 | None — logged to SyncEventLog | Local data failed server validation |

Note: Sync errors are never shown to users. They are logged to SyncEventLog
and the sync is retried. Only if sync consistently fails does the app show
a diagnostic prompt and trigger the SupportReport flow.

---

## User Errors

| Error code | HTTP status | User-facing message | Notes |
|---|---|---|---|
| `user_not_found` | 404 | "User not found." | Internal — should not reach user |
| `user_profile_exists` | 409 | "A profile already exists for this account." | POST /v1/users called when profile already exists |
| `user_display_name_too_long` | 422 | "Display name must be 50 characters or fewer." | Validation |
| `user_goal_invalid` | 422 | "Please select a valid goal." | Invalid enum value |

---

## Rate Limit Errors

| Error code | HTTP status | User-facing message | Notes |
|---|---|---|---|
| `rate_limit_exceeded` | 429 | "Too many requests. Please wait a moment and try again." | General per-user rate limit |
| `rate_limit_auth_exceeded` | 429 | "Too many sign-in attempts. Please wait 60 seconds." | Auth endpoint per-IP limit |

All 429 responses include a `Retry-After` header with seconds to wait.

---

## Biometric Errors

| Error code | HTTP status | User-facing message | Notes |
|---|---|---|---|
| `biometric_consent_required` | 403 | "Please complete the photo consent step to use this feature." | No BiometricConsent record |
| `biometric_consent_declined` | 403 | "You've opted out of this feature. You can enable it in Settings." | Consent record exists with declined status |
| `biometric_consent_write_failed` | 500 | "Something went wrong saving your consent. Please try again." | DB write failure — photo NOT processed |
| `biometric_photo_invalid` | 422 | "Please provide a valid photo." | Photo fails type or size validation |
| `biometric_photo_too_large` | 413 | "Your photo is too large. Please use a smaller image." | Exceeds size limit |

---

## System Errors

| Error code | HTTP status | User-facing message | Notes |
|---|---|---|---|
| `system_error` | 500 | "Something went wrong. We've been notified." | Unhandled exception — Sentry alerted |
| `system_maintenance` | 503 | "PRLifts is temporarily down for maintenance. We'll be back shortly." | Planned maintenance mode |
| `system_database_unavailable` | 503 | "Something went wrong. We've been notified." | Supabase connection failure |

---

## iOS Error Handling Guide

When the iOS app receives an error response, it uses `error_code` to determine
behaviour — not the HTTP status code or the message string.

```swift
enum PRLiftsAPIError: String, Decodable {
    // Auth
    case authTokenInvalid = "auth_token_invalid"
    case authTokenExpired = "auth_token_expired"
    // ... all error codes as cases

    var requiresSignOut: Bool {
        switch self {
        case .authTokenInvalid, .authTokenExpired, .authAccountDeleted: return true
        default: return false
        }
    }

    var userFacingMessage: String {
        // Return the message from the catalog — do not hardcode here
        // This is populated from the API response message field
    }
}
```

**Rules:**
- Never show `error_code` or `request_id` to users
- Always use the `message` field from the API response for user display
- Use `error_code` to determine app behaviour (retry, sign out, show prompt)
- Log `request_id` to the support report if user reports a problem
- `request_id` is the correlation_id — searchable in Railway logs

