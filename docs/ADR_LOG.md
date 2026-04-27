# PRLifts — Architecture Decision Records

**Version:** 1.0
**Last updated:** April 2026
**Owner:** Staff/Principal Engineer
**Audience:** All developers (human and Claude Code)

> Each ADR captures a significant architectural decision: the context,
> the options considered, the decision made, and the consequences.
> The Decision Log in ARCHITECTURE.md captures WHAT was decided.
> This document captures WHY — including alternatives rejected.

---

## ADR-001 — SwiftData over Core Data for local persistence

**Date:** April 2026
**Status:** Accepted
**Deciders:** iOS Platform Lead, Staff Engineer

### Context

The app requires robust offline-first local persistence on iOS.
Two primary options exist in the Apple ecosystem.

### Options Considered

**Option A: SwiftData**
- Native Swift API, declarative, designed for SwiftUI
- Introduced iOS 17 — minimum deployment target must be iOS 17+
- Automatic CloudKit integration available
- Less community documentation than Core Data (newer)

**Option B: Core Data**
- Mature, battle-tested, extensive community documentation
- Objective-C heritage — more verbose in Swift
- Complex to use correctly (context management, merging, etc.)

### Decision

SwiftData. PRLifts targets iOS 17+ as the minimum deployment target.
SwiftData's Swift-native API reduces boilerplate substantially, and the
productivity advantage for a solo developer outweighs Core Data's maturity.

### Consequences

- Minimum iOS version is 17 — users on iOS 16 cannot use the app
- Some SwiftData patterns are not yet well-documented; may need workarounds
- Migration to Core Data is possible but expensive if SwiftData limitations are hit

---

## ADR-002 — FastAPI + Python over Node.js/TypeScript for the backend

**Date:** April 2026
**Status:** Accepted
**Deciders:** Backend Platform Lead, Staff Engineer

### Context

The backend requires async capability for AI operations, strong typing,
and good library support for AI providers.

### Options Considered

**Option A: FastAPI (Python)**
- Excellent async support (asyncio native)
- Pydantic for validation (first-class)
- Anthropic Python SDK is the primary/best-supported SDK
- Strong data science and ML ecosystem if needed later

**Option B: Express / Fastify (Node.js + TypeScript)**
- TypeScript provides type safety
- Large ecosystem
- Anthropic also has a TypeScript SDK
- Would allow sharing types with a web frontend (if added later)

### Decision

FastAPI. The primary consideration is the Anthropic SDK — Python is the
primary language for Anthropic's SDK with the most features and best support.
FastAPI's automatic OpenAPI generation also aligns with our contract-first approach.

### Consequences

- Anthropic SDK is first-class in Python
- type safety provided by Pydantic and mypy
- If a web frontend is added later, there is no type sharing across languages

---

## ADR-003 — Supabase over Firebase for database and auth

**Date:** April 2026
**Status:** Accepted
**Deciders:** Backend Platform Lead, Data Architect

### Context

Need a managed PostgreSQL database with auth, storage, and real-time
capabilities. Must have Row Level Security for data isolation.

### Options Considered

**Option A: Supabase**
- PostgreSQL (standard SQL, full schema control, RLS)
- Open-source — data is not locked in a proprietary format
- Row Level Security at database level
- Self-hosted option available if needed

**Option B: Firebase (Firestore)**
- NoSQL document store — less suited for relational fitness data
- No equivalent of Row Level Security
- Proprietary query language
- Vendor lock-in risk

**Option C: PlanetScale / Neon**
- Standard SQL
- Less integrated (need separate auth solution)

### Decision

Supabase. The fitness data model is inherently relational (Workout → WorkoutExercise → WorkoutSet).
PostgreSQL is the correct data model. Row Level Security at the database level provides
defence-in-depth for user data isolation that NoSQL alternatives cannot match.

### Consequences

- PostgreSQL expertise required
- Supabase free tier has limitations (1GB storage, pause after inactivity)
- Must upgrade to Pro before public launch

---

## ADR-004 — In-process APScheduler over Celery for background jobs (V1)

**Date:** April 2026
**Status:** Accepted
**Deciders:** Backend Platform Lead, DevOps Lead

### Context

Background jobs needed for: job expiry cleanup, daily data purges,
push notification delivery, AI cost summaries.

### Options Considered

**Option A: APScheduler (AsyncIOScheduler, in-process)**
- No additional infrastructure
- Runs in the FastAPI process
- Simple to configure and reason about
- Jobs stop if the service restarts (acceptable — no data loss)

**Option B: Celery + Redis**
- Distributed task queue
- Persistent job queue (survives restarts)
- Requires Redis as broker (additional infrastructure)
- Overkill for V1 job volumes

**Option C: Railway Cron Jobs**
- Railway's built-in cron for HTTP-triggered jobs
- Requires the jobs to be endpoints, not background tasks
- Less integrated with the app code

### Decision

APScheduler for V1. The job cleanup interval is 60 seconds — losing a
single run during a service restart is acceptable (jobs are re-cleaned on
the next run). Celery is the correct V2 upgrade path when job volume
and reliability requirements justify the infrastructure.

### Consequences

- Jobs do not survive service restarts (up to 60-second gap during restart)
- No retry mechanism for failed jobs (logged and retried next interval)
- APScheduler must start inside the FastAPI lifespan context manager (not deprecated startup event)

---

## ADR-005 — Last-write-wins for offline sync conflict resolution

**Date:** April 2026
**Status:** Accepted
**Deciders:** iOS Platform Lead, Data Architect, Staff Engineer

### Context

Users may log workout sets on multiple devices (iPhone + iPad) or have
data that conflicts between local SwiftData and the backend.

### Options Considered

**Option A: Last-write-wins (server timestamp)**
- Simple to implement
- Deterministic
- May silently discard data in edge cases (two devices logging simultaneously)

**Option B: Operational Transform / CRDTs**
- Correct handling of concurrent edits
- Extremely complex to implement
- May be over-engineered for workout logging (rare multi-device concurrent writes)

**Option C: User-visible conflict resolution**
- User chooses which version to keep
- Disruptive — most users should never see a conflict dialog during a workout

### Decision

Last-write-wins using `server_received_at` timestamp. The edge case of
two devices logging the exact same set simultaneously is rare enough that
silent resolution is acceptable. Users can manually correct any discrepancy.

### Consequences

- Rare concurrent writes may silently resolve to the later version
- SyncEventLog records all conflict resolutions for debugging
- No user-visible conflict dialogs during active workouts

---

## ADR-006 — Fail-closed quality gate for future self image generation

**Date:** April 2026
**Status:** Accepted
**Deciders:** Product Architect, ML Platform Lead

### Context

The quality gate uses Claude vision to score face similarity. If the
scoring call itself fails, we must decide what to show the user.

### Options Considered

**Option A: Fail-open (show unscored image)**
- More images shown to users
- Risk: occasionally shows poor quality results
- Future self is an identity-adjacent emotional feature

**Option B: Fail-closed (show fallback message)**
- Some users see a fallback instead of an image when scoring fails
- Better user experience when a poor image would have been shown
- Consistent with the feature's emotional sensitivity

### Decision

Fail-closed. The future self feature is identity-adjacent — the user is
seeing themselves in a transformed state. A poor image (generated but
unscored) can be more harmful to user confidence than a warm fallback
message. The fallback copy ("Your vision is being crafted — check back soon")
is designed to feel like a feature, not a failure.

Quality score null rate is monitored via Sentry to catch systematic
scoring failures that would warrant investigation.

### Consequences

- Some users see a fallback when the scoring call fails
- Null quality score is logged in AIRequestLog for monitoring
- High null rate triggers a Sentry alert

