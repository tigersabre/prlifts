# PRLifts — Operations Runbook

**Version:** 1.0
**Last updated:** April 2026
**Owner:** DevOps Lead
**Audience:** On-call developer (human)

> This is the first document to open when something breaks.
> Each section covers a specific failure scenario: what the symptom
> looks like, how to verify it, and the exact steps to resolve it.
> If something is not covered here, document it after the incident.

---

## Before You Start

1. Check the Sentry dashboard for recent errors
2. Check Railway logs for the API service
3. Check the Supabase dashboard for database health
4. Check Upstash dashboard for Redis health
5. Identify the incident level (P1/P2/P3/P4) using STANDARDS.md §4.2

---

## Section 1 — Service Health Checks

### Is the API running?

```bash
curl https://api.prlifts.app/health
# Expected: {"status": "ok", "timestamp": "..."}
# If 502/503: Railway service is down — see §2
```

### Is the database healthy?

```bash
# Check in Supabase dashboard → Database → Health
# Or via Railway logs — look for connection errors
```

### Is Redis healthy?

```bash
# Check in Upstash dashboard
# Or in Railway logs — look for "Redis connection refused"
```

---

## Section 2 — API Service Down (P1)

**Symptom:** `GET /health` returns 502 or 503. All users affected.

**Steps:**
1. Open Railway dashboard → PRLifts API service → Deployments
2. Check if the latest deployment succeeded
3. If deployment failed: open the deploy logs, find the error
4. If deployment succeeded but service is down: check runtime logs

**Common causes:**

*Startup crash — missing environment variable:*
```
# Look for: KeyError: 'CLAUDE_API_KEY' or similar
# Fix: Add the missing variable in Railway → Variables tab
# Railway will redeploy automatically
```

*Database connection failure on startup:*
```
# Look for: "could not connect to server" or "asyncpg.connect() failed"
# Fix: Verify DATABASE_URL in Railway variables
# Check Supabase project is not paused (free tier pauses after 1 week inactive)
```

*Port binding error:*
```
# Look for: "address already in use"
# Fix: Force redeploy in Railway dashboard
```

**If no obvious cause found:** Roll back to previous deployment in Railway.

---

## Section 3 — Database Issues

### Supabase Free Tier Paused

**Symptom:** All database operations fail. Supabase dashboard shows "Paused."

**Fix:**
1. Log in to Supabase dashboard
2. Click "Restore project"
3. Wait ~2 minutes for restore to complete
4. Verify API health check passes

**Prevention:** Upgrade to Supabase Pro before public launch.

### Connection Pool Exhaustion

**Symptom:** Intermittent 500 errors, Railway logs show "connection pool exhausted."

**Fix:**
1. Verify Railway is using the **pooler** connection string (not direct)
2. If using direct connection: update `DATABASE_URL` to use the pooler URL
3. Reduce `DB_POOL_SIZE` if total connections exceed Supabase limit
4. Consider Supabase Pro upgrade (higher connection limits)

---

## Section 4 — Hung Jobs

**Symptom:** Users report AI features "stuck" — polling indefinitely.
Sentry shows elevated `rows_updated > 0` from `cleanup_expired_jobs`.

**Verify:**
```sql
-- Check for stuck jobs in Supabase SQL editor
SELECT job_type, status, COUNT(*), AVG(EXTRACT(EPOCH FROM (NOW() - created_at))) as avg_age_seconds
FROM job
WHERE status IN ('pending', 'processing')
GROUP BY job_type, status;
```

**Fix:**
1. Check if APScheduler is running: look for `cleanup_expired_jobs` log entries
2. If scheduler not running: Railway service restart (APScheduler restarts with it)
3. If scheduler running but jobs stuck: check Claude API / Fal.ai status pages
4. Manually expire stuck jobs if needed:
```sql
UPDATE job
SET status = 'expired',
    error_message = 'This request took too long. Please try again.',
    completed_at = NOW()
WHERE status IN ('pending', 'processing')
  AND expires_at < NOW();
```

---

## Section 5 — Redis Unavailable

**Symptom:** Railway logs show Redis connection errors. Rate limiting not enforced.

**Impact:** Rate limiting fails open — API functional, but unthrottled.

**Immediate actions:**
1. Verify Upstash dashboard — is the service down?
2. Monitor Anthropic and Fal.ai usage dashboards for unusual spend
3. If Upstash is down: no immediate action required (fail-open is safe short-term)

**If Redis is down for > 1 hour:**
1. Manually check AI usage in Anthropic dashboard
2. Consider temporarily lowering AI monthly limits in ENV_CONFIG to reduce blast radius
3. Contact Upstash support

**Recovery:**
Once Redis is restored, rate limiting resumes automatically. No app restart needed.

---

## Section 6 — AI Provider Outages

### Anthropic Claude API Down

**Symptom:** All insight and benchmarking jobs fail. Sentry shows `AIProviderError`.

**User impact:** Users see "This feature is temporarily unavailable" on AI features.
Core workout logging is unaffected.

**Actions:**
1. Check Anthropic status page: `status.anthropic.com`
2. If confirmed outage: no action needed — jobs fail gracefully with retry messaging
3. If extended (> 2 hours): post status update if you have a status page
4. Jobs do not need manual cleanup — they expire naturally

### Fal.ai Down

**Symptom:** All future_self jobs fail. Same graceful degradation.

**Actions:**
1. Check Fal.ai status
2. If extended outage: same as above
3. No data loss — user can regenerate when service is restored

---

## Section 7 — Secret Rotation

### Rotating Anthropic API Key

```
1. Generate new key in Anthropic dashboard
2. Railway → PRLifts API → Variables → CLAUDE_API_KEY → update value
3. Railway triggers automatic redeploy
4. Verify health check passes after deploy
5. Revoke old key in Anthropic dashboard
6. Log rotation in INCIDENT_LOG.md: "Rotated CLAUDE_API_KEY — routine"
```

### Rotating Fal.ai API Key

Same pattern as Anthropic above, using Fal.ai dashboard.

### Rotating Supabase Service Key

```
⚠ This rotation requires coordination — a brief window where
  the API cannot authenticate to Supabase is possible.

1. Generate new service role key in Supabase dashboard
2. Update SUPABASE_SERVICE_KEY in Railway variables
3. Railway redeploys
4. Verify health check passes
5. Revoke old key in Supabase
```

### Rotating TrustKit Certificate Pin

```
⚠ This requires an iOS app update — users on old builds will
  fail to connect to the backend after the old pin expires.

1. Generate new certificate or wait for renewal
2. Update TrustKit configuration in iOS app with new pin + retain old as backup
3. Release new app build to TestFlight → App Store
4. Wait for > 90% of users to update (check PostHog)
5. Remove old pin in a subsequent release
6. Document rotation in INCIDENT_LOG.md
```

---

## Section 8 — Data Issues

### User Reports Workout Data Missing

1. Identify the user_id from their support report or email
2. Check Supabase directly:
```sql
SELECT COUNT(*) FROM workout WHERE user_id = '[user_id]';
SELECT COUNT(*) FROM workout_set ws
JOIN workout_exercise we ON we.id = ws.workout_exercise_id
JOIN workout w ON w.id = we.workout_id
WHERE w.user_id = '[user_id]';
```
3. If data exists: sync issue — check SyncEventLog for the user
4. If data missing: check backup restore options in Supabase Pro

### Sync Conflict Causing Data Loss

1. Review SyncEventLog for the user for `conflict_resolved` events
2. PRLifts uses last-write-wins — the newer `server_received_at` wins
3. If the wrong version won: restore from Supabase backup (Pro plan required)
4. Document the conflict details for architecture review

---

## Section 9 — Incident Log

Every incident gets a one-line entry here after resolution:

```
[DATE] [SEVERITY] [DURATION] [SUMMARY] [ROOT CAUSE] [RESOLUTION]

2026-04-25 P3 45min API returning 500 on workout-sets endpoint.
  Root cause: Missing database index causing timeout on high set count.
  Resolution: Added idx_workout_set_order, deployed.

2026-04-26 P1 12min Service down after deploy.
  Root cause: Missing APNS_PRIVATE_KEY env var after Railway variable purge.
  Resolution: Restored variable, redeployed.
```

---

## Section 10 — Contacts and Resources

| Resource | URL / Contact |
|---|---|
| Railway dashboard | railway.app |
| Supabase dashboard | app.supabase.com |
| Upstash dashboard | console.upstash.com |
| Anthropic status | status.anthropic.com |
| Sentry dashboard | sentry.io |
| PostHog dashboard | app.posthog.com |
| Apple Developer | developer.apple.com |
| App Store Connect | appstoreconnect.apple.com |

