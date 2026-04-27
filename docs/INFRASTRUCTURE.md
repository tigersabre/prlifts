# PRLifts — Infrastructure Reference

**Version:** 1.0
**Last updated:** April 2026
**Owner:** DevOps Lead
**Audience:** All developers (human and Claude Code)

---

## System Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Devices                             │
│                                                                 │
│   ┌──────────────────┐        ┌──────────────────┐             │
│   │   iPhone / iPad  │        │   iPhone / iPad  │             │
│   │   PRLifts iOS    │        │   PRLifts iOS    │   ...       │
│   └────────┬─────────┘        └────────┬─────────┘             │
└────────────┼───────────────────────────┼─────────────────────  ┘
             │ HTTPS (TLS 1.3)           │
             │ TrustKit CA pinned        │
             ▼                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Railway (US West)                       │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                  PRLifts API Service                     │  │
│   │                                                          │  │
│   │   FastAPI (uvicorn)                                      │  │
│   │   APScheduler (in-process)                               │  │
│   │   ┌────────────┐  ┌────────────┐  ┌────────────────┐   │  │
│   │   │  Routes    │  │  Services  │  │  Background    │   │  │
│   │   │  /v1/*     │  │  layer     │  │  jobs (8 total)│   │  │
│   │   └────────────┘  └────────────┘  └────────────────┘   │  │
│   └──────────────────────────────────────────────────────────┘  │
│          │           │           │           │                   │
└──────────┼───────────┼───────────┼───────────┼──────────────────┘
           │           │           │           │
           ▼           ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────────┐
    │Supabase  │ │ Upstash  │ │Anthrop-│ │   Fal.ai     │
    │(US East) │ │  Redis   │ │  ic    │ │  (image gen) │
    │          │ │          │ │  API   │ │              │
    │PostgreSQL│ │Rate limit│ │Claude  │ │future_self   │
    │Auth      │ │counters  │ │insights│ │generation    │
    │Storage   │ │          │ │quality │ │              │
    │          │ │          │ │scoring │ │⚠ DPA req'd  │
    └──────────┘ └──────────┘ └────────┘ └──────────────┘
           │
           ▼
    ┌──────────────────────────────────────────────────────┐
    │              Supporting Services (no user data)       │
    │   Sentry (errors)    PostHog (analytics/flags)       │
    │   APNs (push)        ExerciseDB (exercise library)   │
    └──────────────────────────────────────────────────────┘
```

---

## Service Details

### PRLifts API (Railway)

| Property | Value |
|---|---|
| **Runtime** | Python 3.12 + uvicorn |
| **Region** | US West (Railway) |
| **Plan** | Railway Hobby → Pro before launch |
| **Always-on** | Yes (required before public launch) |
| **Health check** | `GET /health` → 200 OK |
| **Deploy trigger** | Push to `main` branch |
| **Staging service** | Separate Railway service, same repo |

**Resource configuration:**
```
Memory: 512 MB (upgrade to 1GB at V2 if needed)
CPU: 1 vCPU
Replicas: 1 (V1 — horizontal scaling V2)
```

---

### Supabase

| Property | Value |
|---|---|
| **Plan** | Free → Pro before public launch |
| **Region** | US East (default) |
| **PostgreSQL version** | 15 |
| **Connection pooling** | PgBouncer (built-in) |
| **Backup retention** | 7 days (Pro plan) |
| **Point-in-time recovery** | Pro plan |

**Connection string format:**
```
postgresql+asyncpg://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
```

Use the **pooler** connection string for the application server —
not the direct connection string. This avoids hitting Supabase's
per-project connection limit.

---

### Upstash Redis

| Property | Value |
|---|---|
| **Plan** | Free tier (adequate for V1) |
| **Region** | Match Railway region (US West) |
| **Connection** | `rediss://` (TLS required) |
| **Data** | Rate limit counters only — TTL-based, no persistence required |

---

### Fal.ai

| Property | Value |
|---|---|
| **Access** | REST API over HTTPS |
| **Authentication** | API key in `Authorization` header |
| **Data sent** | User photo + structured prompt |
| **Data retention** | Zero — DPA prohibits retention |
| **DPA** | ⚠ Must be executed before enabling `future_self_enabled` |

---

### Anthropic Claude API

| Property | Value |
|---|---|
| **Access** | REST API over HTTPS |
| **Authentication** | `x-api-key` header |
| **Model** | `claude-sonnet-4-5` (pinned — see MODEL_VERSIONS.md) |
| **Data sent** | Structured workout data only — no PII, no photos |

---

## Network Security

| Connection | Protocol | Protection |
|---|---|---|
| iOS App → Railway API | HTTPS TLS 1.3 | TrustKit certificate pinning (CA level) |
| Railway → Supabase | PostgreSQL TLS | Supabase enforces TLS on all connections |
| Railway → Upstash Redis | `rediss://` TLS | Upstash enforces TLS |
| Railway → Anthropic API | HTTPS TLS 1.3 | Standard TLS |
| Railway → Fal.ai | HTTPS TLS 1.3 | Standard TLS + DPA |
| Railway → APNs | HTTP/2 TLS | Apple's TLS |

---

## Deployment Pipeline

```
Developer push to feature branch
    ↓
GitHub PR opened
    ↓
CI runs (GitHub Actions):
    - pip audit (dependency vulnerability scan)
    - Secret scanning (TruffleHog)
    - Backend tests (pytest, 90% coverage gate)
    - Xcode Cloud triggered:
        - iOS tests (90% coverage gate)
        - TestFlight build (internal)
    ↓
PR reviewed and merged to main
    ↓
Railway auto-deploys to staging
    ↓
Manual verification on staging
    ↓
Railway promotes staging → production (manual trigger)
    ↓
Monitor for 15 minutes (error rate, latency)
    ↓
Done — or rollback if metrics degrade
```

---

## Environments

| Env | API URL | Supabase project | Railway service |
|---|---|---|---|
| Development | `http://localhost:8000` | Dev project | Local |
| Staging | `https://api-staging.prlifts.app` | Staging project | Railway staging |
| Production | `https://api.prlifts.app` | Production project | Railway production |

**Staging and production always use separate Supabase projects.**
Never point staging at production data.

---

## Scaling Plan

| Trigger | Action |
|---|---|
| Response p95 latency > 2s | Investigate before scaling |
| Supabase connection errors | Upgrade connection pool size |
| Railway memory > 80% sustained | Upgrade to 1GB instance |
| > 10,000 monthly active users | Add Railway replica + Redis Celery (V2) |
| > 100,000 MAU | Full infrastructure review |

