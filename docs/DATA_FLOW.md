# PRLifts — Data Flow Diagram

**Version:** 1.0
**Last updated:** April 2026
**Owners:** Data Architect + Security Architect
**Audience:** All developers (human and Claude Code)

> This document maps every data flow between systems — what data moves,
> in which direction, triggered by what, and what security controls apply.
> It is the reference for understanding how data moves through the system
> and for verifying that sensitive data is handled correctly at every hop.

---

## System Components

```
User Device (iOS)
    │
    ├── SwiftData (local store)
    └── PRLifts iOS App
            │
            ▼
    PRLifts Backend (FastAPI / Railway)
            │
            ├── Supabase PostgreSQL (primary data store)
            ├── Supabase Storage (image storage)
            ├── Upstash Redis (rate limiting)
            ├── Anthropic Claude API (text AI)
            └── Fal.ai (image generation)

Supporting services (no user data):
    ├── Sentry (error reporting — anonymised)
    ├── PostHog (analytics — anonymised)
    └── APNs (push notifications — device tokens only)
```

---

## Flow 1 — User Authentication

**Trigger:** User taps Sign in with Apple / Google / email

```
iOS App
  → Auth provider (Apple / Google)
      → Returns: identity token
  → Supabase Auth (via backend)
      → Returns: JWT access token + refresh token
  → iOS Keychain (stores tokens — never UserDefaults)
```

**Data transmitted:** Identity token (Apple/Google), email (optional),
display name (optional)

**Security controls:**
- TLS 1.3 in transit
- JWT short-lived (configurable, Supabase default)
- Tokens stored in iOS Keychain only
- Email nullable — Apple relay address or absent is valid

---

## Flow 2 — Workout Set Logging (Online)

**Trigger:** User taps "Log Set" on ActiveWorkoutScreen

```
iOS App
  → SwiftData (write local first — immediate)
      → SyncEventLog entry: write_attempt
  → Backend POST /v1/workout-sets
      → Supabase PostgreSQL (upsert on id)
      → PR detection service
          → If PR detected: PersonalRecord upsert
      → Returns: WorkoutSetResponse (with is_personal_record flag)
  → SwiftData (update sync status)
      → SyncEventLog entry: sync_success
  → If PR: POST /v1/jobs (type: insight)
      → Returns: job_id (HTTP 202)
```

**Data transmitted:** WorkoutSet fields (weight, reps, rpe, etc.),
workout_exercise_id, user authentication token

**Security controls:**
- RLS: workout_exercise must belong to authenticated user
- Rate limit: 100 req/min/user (Upstash Redis)
- Input validation: all numeric fields have explicit bounds

---

## Flow 3 — Workout Set Logging (Offline)

**Trigger:** User taps "Log Set" when network unavailable

```
iOS App
  → SwiftData (write local — immediate)
      → SyncEventLog entry: write_attempt
  → Sync queued — NWPathMonitor watching for connectivity

[Later — on connectivity restored]

NWPathMonitor callback (background thread → dispatch to main)
  → Backend POST /v1/workout-sets (upsert on id — idempotent)
      → Same flow as online (Flow 2)
  → SyncEventLog entry: sync_success (or sync_failure if backend error)
```

**Data at rest while offline:** WorkoutSet in SwiftData (encrypted by iOS
Data Protection), SyncEventLog entry with status pending

---

## Flow 4 — AI Workout Insight Generation

**Trigger:** Workout completed, insight Job created

```
Backend POST /v1/jobs (type: insight)
  → Job record created (status: pending)
  → Returns: job_id (HTTP 202)

[FastAPI BackgroundTask runs]

Backend
  → Supabase: fetch Workout + WorkoutSets + User.goal + User.unit_preference
  → Supabase: fetch active PromptTemplate (feature: insight)
  → PromptTemplate: interpolate structured workout data
      ⚠ User-provided text (workout name, notes) is summarised
        by preprocessing — never interpolated directly
  → Anthropic Claude API
      → Request: structured prompt (no raw user text)
      → Response: insight text (max 280 characters)
  → Validate response against ai_forbidden_phrases.txt
  → AIRequestLog: store prompt_template_id, response, quality_score: null,
    duration_ms (30-day retention, admin-only table)
  → Job record updated (status: complete, result: insight text)

iOS App (polling GET /v1/jobs/{job_id})
  → Receives: complete status + insight text
  → Displays on WorkoutCompleteScreen
```

**Data transmitted to Claude API:** Structured workout data only —
exercise names, weights, reps, sets, RPE values, user goal, unit preference.
No user name, email, photo, or free-text user input.

**Security controls:**
- Rate limit: 10 AI req/min/user combined
- Monthly limit: 60 insights/user/month
- Response validation before display
- AI data logged to admin-only table, 30-day retention

---

## Flow 5 — Future Self Image Generation

**Trigger:** User submits photo on PhotoCaptureScreen

This flow has the most sensitive data handling in the system.
Every step is documented explicitly.

```
Step 1 — Consent verification
iOS App
  → Backend: verify BiometricConsent exists and is accepted for this user
  → If no consent: reject request, return to BiometricConsentScreen

Step 2 — Photo submission
iOS App
  → Backend POST /v1/jobs (type: future_self)
      Payload: photo (base64), user_id (from JWT)
  → Job record created (status: pending)
  → Returns: job_id (HTTP 202)
  ⚠ Photo is in transit — TLS 1.3, certificate-pinned on iOS

Step 3 — Image generation (FastAPI BackgroundTask)
Backend receives photo
  → Photo is held in memory only — never written to Railway filesystem
  → Fetch User.goal, User.gender from Supabase
  → Fetch active PromptTemplate (feature: future_self)
  → Fal.ai API call 1: generate variation 1
      Request: photo + structured prompt (goal, gender — no user name/email)
      Response: generated image 1
  → Fal.ai API call 2: generate variation 2
      Request: photo + same prompt
      Response: generated image 2
  ⚠ Photo is forwarded to Fal.ai over TLS — never logged, never stored locally

Step 4 — Photo deletion
  → Original photo deleted from memory immediately after both Fal.ai calls
  → Total time from receipt to deletion: target < 60 seconds
  ⚠ Automated CI test verifies photo absent within 60 seconds

Step 5 — Quality gate
Backend
  → Anthropic Claude API (vision): score variation 1 face similarity (1–10)
  → Anthropic Claude API (vision): score variation 2 face similarity (1–10)
  → If highest score >= 6: proceed with highest-scoring variation
  → If both scores < 6: job status = failed, result = quality_gate_failed
  → If scoring call itself fails: job status = failed (fail-closed),
    quality_score = null logged, Sentry alert if null rate exceeds threshold

Step 6 — Image storage
Backend
  → Winning variation stored in Supabase Storage (private bucket)
  → Signed URL generated (time-limited)
  → AIRequestLog: prompt_template_id, quality_score, duration_ms (admin-only)
  → Job record: status = complete, result = {image_url: signed_url}

Step 7 — Client retrieval
iOS App (polling GET /v1/jobs/{job_id})
  → Receives: complete status + signed image URL
  → Displays content warning before reveal
  → FutureSelfRevealScreen: image displayed with celebration state

Step 8 — Notification attachment
Backend (async, after job complete)
  → Image URL attached to show-up nudge APNs payload
  → APNs delivers rich notification with image attachment
```

**Data transmitted to Fal.ai:** User photo + structured prompt
(goal category + gender category — no name, email, or free text)

**Data retained after flow:**
- Original photo: DELETED within 60 seconds
- Generated image: stored in Supabase Storage (user-owned, deletable)
- AIRequestLog: prompt version + quality score (admin-only, 30-day retention)
- Job record: status + image URL reference

**Security controls:**
- BiometricConsent required before any photo accepted
- Photo never written to disk on Railway
- Fal.ai DPA executed before any photo processed
- TLS 1.3 + certificate pinning (iOS) for photo transmission
- Supabase Storage private bucket — signed URLs only, time-limited
- RLS: user can only access their own images

---

## Flow 6 — Push Notification Delivery

**Trigger:** PR detected, workout reminder time reached, show-up nudge conditions met

```
Backend
  → Determine notification type and target user
  → Fetch device token for user (stored in Supabase)
  → Construct APNs payload (see NOTIFICATIONS.md for exact payload structures)
  → APNs HTTP/2 API
      → Payload: notification type, title, body, deep link URL, image URL (if nudge)
  → APNs → User device
  → iOS: display notification

[User taps notification]

iOS
  → Universal Link handler resolves deep link
  → Navigate to target screen (see DEEP_LINKS.md)
```

**Data transmitted to APNs:** Device token, notification content (title, body),
deep link URL, image URL (for show-up nudge — references Supabase Storage signed URL)

**Note:** APNs receives device tokens and notification content.
Apple's privacy policy governs APNs data handling. No PII is transmitted
in notification payloads — user is identified by device token only.

---

## Flow 7 — Sync Event Log Upload

**Trigger:** Sync failure detected, or user taps "Report a problem"

```
iOS App
  → Fetch SyncEventLog entries where uploaded_at IS NULL
  → Backend POST /v1/support/sync-log
      Payload: array of SyncEventLog entries (no PII — only entity IDs and event types)
  → Supabase: SyncEventLog entries stored (linked to user_id)
  → iOS: update local entries with uploaded_at timestamp
```

**Data transmitted:** SyncEventLog entries (entity_id, event_type, occurred_at, detail).
No workout content — only metadata about sync operations.

---

## Flow 8 — Support Report Submission

**Trigger:** User taps "Report a problem" in Settings

```
iOS App
  → Collect: device_model, ios_version, app_version, user description
  → Optionally trigger Flow 7 (sync log upload)
  → Backend POST /v1/support/reports
  → Supabase: SupportReport stored
  → Support inbox notified
```

**Data transmitted:** Anonymous user_id, device info, app version,
user-written description. No PII unless user includes it in description.

---

## Data Classification Summary

| Data type | Classification | Stored | Transmitted to | Retention |
|---|---|---|---|---|
| Auth tokens | Sensitive | iOS Keychain | Supabase Auth | Session lifetime |
| Workout data | Personal | SwiftData + Supabase | Backend only | Until account deletion |
| User photo | Biometric | Memory only (transit) | Fal.ai (transient) | < 60 seconds |
| Generated image | Personal | Supabase Storage | Client (signed URL) | Until deleted by user |
| AI prompts/responses | Internal | AIRequestLog (admin) | Claude API | 30 days |
| Quality scores | Internal | AIRequestLog (admin) | None | 30 days |
| Device tokens | Operational | Supabase | APNs | Until token refresh |
| Sync events | Diagnostic | SwiftData + Supabase | Backend (on demand) | Until account deletion |
| Crash reports | Diagnostic | Sentry | Sentry | Per Sentry policy |
| Analytics events | Analytical | PostHog | PostHog | Per PostHog policy |

