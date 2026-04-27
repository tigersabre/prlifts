# PRLifts — Background Job Catalog

**Version:** 1.0
**Last updated:** April 2026
**Owners:** Backend Platform Lead + DevOps Lead
**Audience:** All developers (human and Claude Code)

> Every scheduled and background task is documented here.
> If you add a new background job, add it here first.
> This document is the authoritative reference for what runs,
> when, what it does, and what happens when it fails.

---

## Job Runtime

All background jobs run via APScheduler AsyncIOScheduler, started
in the FastAPI `lifespan` context manager. See STANDARDS.md §7.6
for the correct startup pattern.

```python
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(cleanup_expired_jobs, "interval", seconds=60,
                      id="cleanup_expired_jobs")
    scheduler.add_job(purge_expired_ai_logs, "cron", hour=2, minute=0,
                      id="purge_ai_logs")
    # ... all jobs registered here
    scheduler.start()
    yield
    scheduler.shutdown()
```

If the Railway service restarts, all scheduled jobs restart with it.
Hung jobs from the previous service run are cleaned up within 60 seconds
of the scheduler starting. No data loss occurs.

---

## Job Catalog

### JOB-001 — cleanup_expired_jobs

| Field | Value |
|---|---|
| **ID** | `cleanup_expired_jobs` |
| **Schedule** | Every 60 seconds |
| **Purpose** | Set jobs past their TTL to `expired` status |
| **Idempotent** | Yes — running twice has no additional effect |
| **Failure behaviour** | Logs ERROR, retries next interval |

**What it does:**
```python
async def cleanup_expired_jobs():
    """
    Sets any job in 'pending' or 'processing' state that has passed
    its expires_at timestamp to 'expired' status.

    This prevents clients from polling indefinitely for jobs that
    will never complete (e.g., due to provider failure or service restart).
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(Job)
        .where(Job.status.in_(["pending", "processing"]))
        .where(Job.expires_at < now)
        .values(
            status="expired",
            error_message="This request took too long. Please try again.",
            completed_at=now
        )
    )
    logger.info("Expired job cleanup complete",
                rows_updated=result.rowcount)
```

**Monitoring:** Log `rows_updated > 0` frequently (> 5/minute) is a WARNING —
indicates jobs are failing to complete within their TTL.

---

### JOB-002 — purge_expired_ai_logs

| Field | Value |
|---|---|
| **ID** | `purge_ai_logs` |
| **Schedule** | Daily at 02:00 UTC |
| **Purpose** | Delete AIRequestLog rows past their 30-day retention window |
| **Idempotent** | Yes |
| **Failure behaviour** | Logs ERROR, retries next night |

**What it does:**
```python
async def purge_expired_ai_logs():
    """
    Deletes ai_request_log rows where expires_at < NOW().
    30-day retention enforced automatically.
    """
    result = await db.execute(
        delete(AIRequestLog).where(AIRequestLog.expires_at < datetime.now(timezone.utc))
    )
    logger.info("AI log purge complete", rows_deleted=result.rowcount)
```

---

### JOB-003 — purge_old_jobs

| Field | Value |
|---|---|
| **ID** | `purge_old_jobs` |
| **Schedule** | Daily at 02:15 UTC |
| **Purpose** | Delete completed/failed/expired job records older than 7 days |
| **Idempotent** | Yes |
| **Failure behaviour** | Logs ERROR, retries next night |

**What it does:**
```python
async def purge_old_jobs():
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    result = await db.execute(
        delete(Job)
        .where(Job.status.in_(["complete", "failed", "expired"]))
        .where(Job.completed_at < cutoff)
    )
    logger.info("Old job purge complete", rows_deleted=result.rowcount)
```

---

### JOB-004 — purge_old_support_reports

| Field | Value |
|---|---|
| **ID** | `purge_support_reports` |
| **Schedule** | Daily at 02:30 UTC |
| **Purpose** | Delete support reports older than 90 days |
| **Idempotent** | Yes |
| **Failure behaviour** | Logs ERROR, retries next night |

---

### JOB-005 — send_workout_reminders

| Field | Value |
|---|---|
| **ID** | `workout_reminders` |
| **Schedule** | Every hour at :00 |
| **Purpose** | Send scheduled workout reminder notifications |
| **Idempotent** | Yes — tracks sent_today flag to prevent duplicate sends |
| **Failure behaviour** | Logs WARNING, individual user failures do not stop the batch |

**What it does:**
Finds users whose configured reminder time falls within the current hour,
in their timezone, on their configured days, and who have not received
a reminder today. Sends APNs push notification to each.

**Key safety check:** Always verify `reminder_sent_today = false` before
sending — scheduler restart or duplicate invocation must not send twice.

---

### JOB-006 — send_show_up_nudges

| Field | Value |
|---|---|
| **ID** | `show_up_nudges` |
| **Schedule** | Every hour at :30 |
| **Purpose** | Send motivational nudge notifications on workout days with no workout logged |
| **Idempotent** | Yes — one nudge per user per day maximum |
| **Failure behaviour** | Logs WARNING, individual user failures do not stop the batch |

**Trigger conditions (all must be true):**
1. Today is a configured workout day for the user
2. Current time has passed the user's nudge time (in their timezone)
3. No workout started today (any status)
4. Nudge not already sent today
5. User has push notification permission

---

### JOB-007 — daily_ai_cost_summary

| Field | Value |
|---|---|
| **ID** | `daily_ai_cost` |
| **Schedule** | Daily at 00:05 UTC (5 minutes after midnight) |
| **Purpose** | Aggregate yesterday's AI usage into daily_ai_cost table |
| **Idempotent** | Yes — upsert on date |
| **Failure behaviour** | Logs ERROR, data is not lost (AIRequestLog still has it) |

**What it records:**
- Total Claude API input tokens
- Total Claude API output tokens
- Total Fal.ai image generation calls
- Total Claude vision scoring calls
- Total jobs by type
- Estimated cost (calculated from published pricing)

Used for the paywall decision at V2 and for circuit breaker monitoring.

---

### JOB-008 — cleanup_orphaned_storage

| Field | Value |
|---|---|
| **ID** | `cleanup_orphaned_storage` |
| **Schedule** | Weekly, Sunday at 03:00 UTC |
| **Purpose** | Find and delete Supabase Storage objects with no matching user record |
| **Idempotent** | Yes |
| **Failure behaviour** | Logs ERROR — storage leak is not a user-facing issue, retries next week |

**What it does:**
Lists all objects in the future self image bucket. For each object,
checks that the owning user_id still exists in the `user` table.
Deletes any orphaned objects (user deleted but storage not cleaned up).

---

## Job Monitoring

All jobs log at INFO on completion:
```python
logger.info(
    "Job complete",
    job_name="cleanup_expired_jobs",
    duration_ms=elapsed,
    rows_affected=count,
    next_run=scheduler.get_job("cleanup_expired_jobs").next_run_time
)
```

**Alerting thresholds (Sentry):**
- Any job logging at ERROR level → Sentry capture
- Any job not running for > 2x its expected interval → Sentry alert (V2)

**RUNBOOK.md references:**
- JOB-001 failure: see RUNBOOK.md § Hung Jobs
- JOB-005/006 failure: see RUNBOOK.md § Notification Delivery Failures


---

### JOB-009 — purge_expired_biometric_consent

| Field | Value |
|---|---|
| **ID** | `purge_biometric_consent` |
| **Schedule** | Weekly, Sunday at 04:00 UTC |
| **Purpose** | Delete BiometricConsent records where user was deleted more than 1 year ago |
| **Idempotent** | Yes |
| **Failure behaviour** | Logs ERROR — legal data, requires manual investigation if job fails |

**What it does:**
```python
async def purge_expired_biometric_consent():
    """
    Deletes biometric_consent rows where user_deleted_at is set and
    more than 1 year has passed. These records are retained post-deletion
    for BIPA legal compliance and purged after the required retention window.

    biometric_consent uses ON DELETE RESTRICT — this job is the only
    mechanism that deletes these rows. Account deletion sets user_deleted_at
    but does NOT delete the row.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=365)
    result = await db.execute(
        delete(BiometricConsent)
        .where(BiometricConsent.user_deleted_at < cutoff)
    )
    logger.info("Biometric consent purge complete", rows_deleted=result.rowcount)
```

**Important:** Any failure of this job must be investigated — it is a legal
compliance requirement. Alert on ERROR log from this job.

---

### JOB-010 — reset_daily_notification_flags

| Field | Value |
|---|---|
| **ID** | `reset_notification_flags` |
| **Schedule** | Daily at 00:01 UTC |
| **Purpose** | Reset `reminder_sent_today` and `nudge_sent_today` flags to false |
| **Idempotent** | Yes |
| **Failure behaviour** | Logs ERROR — if this fails, no notifications are sent that day (safe failure) |

**What it does:**
Resets both flags to `false` on all `user_notification_preference` rows.
Must run before JOB-005 and JOB-006 for the day. Scheduled at 00:01 UTC
to ensure it completes before the first notification window.

```python
async def reset_daily_notification_flags():
    await db.execute(
        update(UserNotificationPreference)
        .values(
            reminder_sent_today=False,
            nudge_sent_today=False,
            last_reset_date=date.today()
        )
    )
    logger.info("Daily notification flags reset complete")
```

