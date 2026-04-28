# PRLifts — Environment Configuration Reference

**Version:** 1.0
**Last updated:** April 2026
**Owner:** DevOps Lead
**Audience:** All developers (human and Claude Code)

> Every environment variable the backend uses is documented here.
> This is the complete operational reference — not just secrets,
> but all configuration that varies between environments.
> The `.env.example` file in the repository mirrors this document.

---

## Environments

| Environment | Railway service | Purpose |
|---|---|---|
| `development` | Local machine | Local development and debugging |
| `test` | Local machine / CI | Automated test suite |
| `staging` | Railway staging | Pre-production verification |
| `production` | Railway production | Live user traffic |

---

## Required Variables (All Environments)

These must be set in every environment. The backend will not start without them.

### Database

| Variable | Format | Example | Notes |
|---|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:port/db` | See below | Async SQLAlchemy URL. Must use `asyncpg` driver. |

**Per environment:**
```
development: postgresql+asyncpg://postgres:postgres@localhost:5432/prlifts_dev
test:        postgresql+asyncpg://prlifts_test_user:pass@localhost:5432/prlifts_test
staging:     postgresql+asyncpg://...supabase.co/postgres (Railway env var)
production:  postgresql+asyncpg://...supabase.co/postgres (Railway env var)
```

### Redis

| Variable | Format | Notes |
|---|---|---|
| `REDIS_URL` | `redis://host:port/db` | Upstash uses `rediss://` (TLS) in staging/production |

```
development: redis://localhost:6379/0
test:        redis://localhost:6379/1      (separate DB from dev)
staging:     rediss://...upstash.io:6379  (Railway env var)
production:  rediss://...upstash.io:6379  (Railway env var)
```

### Supabase

| Variable | Description | Notes |
|---|---|---|
| `SUPABASE_URL` | Your Supabase project URL | `https://your-project.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Service role key | **Secret.** Bypasses RLS — never expose to client |
| `SUPABASE_JWT_SECRET` | JWT signing secret | Used to verify user JWTs from Supabase Auth |

### Application

| Variable | Values | Default | Notes |
|---|---|---|---|
| `ENVIRONMENT` | `development`, `test`, `staging`, `production` | — | Required. Controls logging, AI mocking, seed data. |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` | `DEBUG` in development only. Never in production. |
| `APP_VERSION` | Semver string | `0.1.0` | Set in Railway from Git tag. |

---

## AI Provider Variables

These are secrets. Stored in Railway environment variables.
Never in `.env` files that might be committed.

| Variable | Provider | Notes |
|---|---|---|
| `CLAUDE_API_KEY` | Anthropic | `sk-ant-...` prefix. Rotate via Anthropic dashboard. |
| `FAL_AI_API_KEY` | Fal.ai | Rotate via Fal.ai dashboard. |
| `EXERCISEDB_API_KEY` | RapidAPI / ExerciseDB | Used only during exercise seeding. |

### AI Configuration

| Variable | Default | Notes |
|---|---|---|
| `AI_PROVIDERS_MOCKED` | `false` | Set `true` in test environment. Prevents real API calls in tests. |
| `AI_MAX_MONTHLY_INSIGHTS` | `60` | Per-user monthly insight limit. |
| `AI_MAX_MONTHLY_IMAGES` | `5` | Per-user monthly image generation limit. |
| `AI_DAILY_SPEND_LIMIT_USD` | `50` | Circuit breaker threshold. Disables AI if exceeded. |

---

## Observability Variables

| Variable | Notes |
|---|---|
| `SENTRY_DSN` | Sentry project DSN. Set in Railway + Xcode Cloud. |
| `POSTHOG_API_KEY` | PostHog project API key for feature flags and analytics. |
| `POSTHOG_HOST` | Default: `https://app.posthog.com`. Override for EU instance. |

---

## APNs (Push Notifications)

| Variable | Notes |
|---|---|
| `APNS_KEY_ID` | Apple Push Notification key ID from Apple Developer |
| `APNS_TEAM_ID` | Apple Developer Team ID |
| `APNS_PRIVATE_KEY` | Contents of the `.p8` key file (multiline — Railway handles this) |
| `APNS_BUNDLE_ID` | iOS app bundle ID: `app.prlifts` |
| `APNS_ENVIRONMENT` | `sandbox` (development/staging) or `production` |

---

## Optional Variables (Defaults Apply if Absent)

| Variable | Default | Notes |
|---|---|---|
| `API_HOST` | `0.0.0.0` | FastAPI host binding |
| `API_PORT` | `8000` | FastAPI port |
| `API_WORKERS` | `1` | Uvicorn worker count. Railway auto-scales. |
| `DB_POOL_SIZE` | `10` | SQLAlchemy connection pool size |
| `DB_MAX_OVERFLOW` | `20` | Max additional connections above pool_size |
| `RATE_LIMIT_GENERAL` | `100` | Requests per minute per user (general endpoints) |
| `RATE_LIMIT_AI` | `10` | Requests per minute per user (AI endpoints combined) |
| `RATE_LIMIT_AUTH` | `5` | Attempts per minute per IP (auth endpoints) |
| `JOB_TTL_MINUTES` | `5` | Minutes before a pending/processing job expires |
| `JOB_CLEANUP_INTERVAL_SECONDS` | `60` | How often the job cleanup task runs |
| `AI_RESPONSE_MAX_LENGTH` | `280` | Maximum characters in an AI insight response |
| `PHOTO_DELETION_TIMEOUT_SECONDS` | `60` | Maximum seconds before photo must be deleted |

---

## `.env.example` Template

```env
# Copy this file to .env (development) or .env.test (test)
# Never commit either file — they are in .gitignore

# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG
APP_VERSION=0.1.0

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/prlifts_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here
SUPABASE_JWT_SECRET=your-jwt-secret-here

# AI Providers (use real keys for development, 'test_key' for tests)
CLAUDE_API_KEY=sk-ant-your-key-here
FAL_AI_API_KEY=your-fal-key-here
EXERCISEDB_API_KEY=your-rapidapi-key-here

# AI Configuration
AI_PROVIDERS_MOCKED=false
AI_MAX_MONTHLY_INSIGHTS=60
AI_MAX_MONTHLY_IMAGES=5
AI_DAILY_SPEND_LIMIT_USD=50

# Observability (optional in development)
SENTRY_DSN=
POSTHOG_API_KEY=
POSTHOG_HOST=https://app.posthog.com

# APNs (required for notification testing)
APNS_KEY_ID=
APNS_TEAM_ID=
APNS_PRIVATE_KEY=
APNS_BUNDLE_ID=app.prlifts
APNS_ENVIRONMENT=sandbox
```

---

## Railway Configuration

In Railway, environment variables are set per service per environment
(staging vs production). Never share environment variables between
the staging and production services.

## Service URLs

| Environment | URL |
|---|---|
| Staging | `https://prlifts-production.up.railway.app` |
| Production | TBD — configured before public launch |

**Setting a variable in Railway:**
1. Select the service (PRLifts API)
2. Variables tab
3. Add or update the variable
4. Deploy is triggered automatically

**Rotating a secret:**
1. Generate new key/secret in the provider dashboard
2. Update the Railway variable
3. Railway triggers a redeploy
4. Verify the service starts cleanly (health check passes)
5. Revoke the old key in the provider dashboard

Full rotation procedures are in RUNBOOK.md § Secret Rotation.

---

## Xcode Cloud Configuration

The iOS app requires these variables set in Xcode Cloud:

| Variable | Notes |
|---|---|
| `SENTRY_DSN` | Same DSN as backend — different project if desired |
| `API_BASE_URL_STAGING` | `https://api-staging.prlifts.app/v1` |
| `API_BASE_URL_PRODUCTION` | `https://api.prlifts.app/v1` |
| `POSTHOG_API_KEY` | PostHog key for iOS analytics |

These are set via Xcode Cloud environment variables, not in code or `.env` files.

