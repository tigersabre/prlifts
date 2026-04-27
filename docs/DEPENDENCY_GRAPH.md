# PRLifts — Service Dependency Graph

**Version:** 1.0
**Last updated:** April 2026
**Owner:** DevOps Lead + Software Architect
**Audience:** All developers (human and Claude Code)

> This document defines what depends on what, and what happens
> to the system if any component becomes unavailable.
> Used for incident response: when something breaks, check here first
> to understand the blast radius before investigating.

---

## Dependency Map

```
iOS App
  ├── REQUIRED: PRLifts Backend API
  │     ├── REQUIRED: Supabase PostgreSQL
  │     │     └── if unavailable: ALL endpoints fail
  │     ├── REQUIRED: Supabase Auth
  │     │     └── if unavailable: Login fails, existing sessions continue (JWT cached)
  │     ├── REQUIRED: Upstash Redis
  │     │     └── if unavailable: Rate limiting fails OPEN (requests proceed)
  │     ├── OPTIONAL: Anthropic Claude API
  │     │     └── if unavailable: AI insight and benchmarking jobs fail gracefully
  │     ├── OPTIONAL: Fal.ai
  │     │     └── if unavailable: future_self jobs fail gracefully
  │     └── OPTIONAL: APNs
  │           └── if unavailable: notifications not delivered (silent failure)
  │
  ├── OPTIONAL: Sentry (crash reporting)
  │     └── if unavailable: crashes not reported, app unaffected
  └── OPTIONAL: PostHog (analytics + feature flags)
        └── if unavailable: fallback to beta_tier on User (see Feature Flags)
```

---

## Failure Impact Table

| Component | Type | Impact if unavailable | Degradation |
|---|---|---|---|
| Supabase PostgreSQL | Required | All API endpoints fail | Full outage |
| Supabase Auth | Required for login | Sign-in fails; existing JWT sessions continue | Partial |
| Supabase Storage | Required for future self | Future self image cannot be stored or retrieved | Feature-level |
| PRLifts Backend | Required | All network features fail; app works offline | Major |
| Upstash Redis | Required for rate limiting | Rate limiting fails open (requests proceed unthrottled) | Security degradation only |
| Anthropic Claude API | Optional | AI insights and benchmarking fail; PR detection unaffected | Feature-level |
| Fal.ai | Optional | Future self generation fails; all other features unaffected | Feature-level |
| APNs | Optional | Push notifications not delivered; app fully functional | Feature-level |
| Sentry | Optional | Errors not captured remotely; app unaffected | Observability only |
| PostHog | Optional | Feature flags fall back to beta_tier; analytics not captured | Minor |

---

## Dependency Detail: Upstash Redis Failure

If Upstash Redis becomes unavailable, the rate limiting middleware
cannot check or increment counters. **The configured behaviour is
fail-open** — requests proceed without rate limiting.

This is the correct trade-off: failing closed would make the entire
API unavailable when Redis is down, which is worse than temporarily
unthrottled requests.

**Risk during Redis outage:** Motivated attacker could exhaust AI API
credits. Monitor Anthropic/Fal.ai usage dashboards during any Redis outage.

**Runbook action:** See RUNBOOK.md § Redis Unavailable.

---

## Dependency Detail: PostHog Failure

If PostHog is unavailable:
1. Feature flag checks fall back to `User.beta_tier` database column
2. Analytics events are dropped (not queued for later)
3. App continues to function normally

The `beta_tier` fallback ensures premium features remain accessible
to authorised users even if PostHog is down.

---

## Dependency Detail: Anthropic Claude API Failure

If the Claude API is unavailable or returns errors:
1. New AI insight jobs: status set to `failed`, user sees fallback message
2. Quality gate scoring calls fail → fail-closed → future_self job fails gracefully
3. Existing completed job results are unaffected — already stored in DB
4. Workout logging, PR detection, and sync continue normally

The circuit breaker auto-disables `ai_insights_enabled` if the daily
spend threshold is exceeded (not the same as an outage, but similar
user-facing behaviour).

---

## Dependency Detail: Fal.ai Failure

If Fal.ai is unavailable:
1. New future_self jobs: status set to `failed`, user sees warm fallback
2. All other features unaffected
3. Existing generated images are already in Supabase Storage — unaffected

---

## Critical Path: Workout Logging (Core Feature)

The workout logging critical path requires only:
- iOS SwiftData (local, always available)
- Backend API (for sync)
- Supabase PostgreSQL

If any of the above is unavailable:
- **SwiftData down:** Impossible — local storage is always available
- **Backend API down:** Sets log offline, syncs when reconnected
- **Supabase down:** Backend API returns 503, iOS queues for retry

**Workout logging is the most resilient feature** — it functions fully
offline and syncs when connectivity + backend are both available.

---

## Critical Path: Future Self Generation

The future self generation requires ALL of:
1. iOS App (available)
2. Backend API (available)
3. Supabase PostgreSQL — BiometricConsent verification + Job creation
4. Fal.ai — image generation (×2)
5. Anthropic Claude API — quality scoring (×1)
6. Supabase Storage — image storage

This is the most fragile flow in the system — it has the most external
dependencies. Failures at any step surface as a warm fallback message.

---

## V2 Dependencies (Not Yet in Scope)

When these are added, this document must be updated:

| Component | Adds dependency on |
|---|---|
| Celery + Redis | Redis becomes required for async jobs |
| Cloudflare R2 | Additional storage dependency |
| Stripe | Payment provider dependency for paywall |
| Garmin/Whoop/Oura APIs | Third-party health data APIs |

