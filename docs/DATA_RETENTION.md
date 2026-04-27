# PRLifts — Data Retention Schedule

**Version:** 1.0
**Last updated:** April 2026
**Owner:** Privacy Counsel / Data Architect
**Audience:** All developers, legal, support

> Every data type collected by PRLifts has a defined retention period
> and a defined deletion mechanism. This document is the source of truth
> for what is kept, how long, and how it is deleted.
> It is referenced in the Privacy Policy and the Third Party Processor Register.

---

## Retention Principles

1. **Keep only what is needed.** If a data type is not actively used by a
   feature, the default is to not collect it.
2. **Delete promptly.** Retention periods are maximums, not targets.
3. **Automate deletion.** Manual deletion processes fail — all retention
   limits are enforced by scheduled tasks, not human memory.
4. **Log deletion.** Every automated deletion run is logged with record counts.

---

## Retention Schedule

### User Account Data

| Data type | Location | Retention | Deletion mechanism |
|---|---|---|---|
| User profile (name, email, preferences) | Supabase `user` table | Until account deletion | CASCADE DELETE on `user` row |
| Auth tokens (JWT) | Supabase Auth | Session lifetime (configurable) | Auto-expired by Supabase Auth |
| Auth tokens (iOS Keychain) | iOS device | Until sign-out or app uninstall | Keychain cleared on sign-out |

---

### Workout Data

| Data type | Location | Retention | Deletion mechanism |
|---|---|---|---|
| Workouts | Supabase `workout` | Until account deletion | CASCADE DELETE on `user` row |
| WorkoutExercises | Supabase `workout_exercise` | Until account deletion | CASCADE DELETE via workout |
| WorkoutSets | Supabase `workout_set` | Until account deletion | CASCADE DELETE via workout_exercise |
| PersonalRecords | Supabase `personal_record` | Until account deletion | CASCADE DELETE on `user` row |
| Local SwiftData cache | iOS device | Until account deletion or app uninstall | Cleared on account deletion |

---

### AI Data

| Data type | Location | Retention | Deletion mechanism |
|---|---|---|---|
| AI request log (prompts + responses) | Supabase `ai_request_log` | 30 days | APScheduler nightly task: `DELETE WHERE expires_at < NOW()` |
| Quality scores | Supabase `ai_request_log` | 30 days (with log row) | Same as above |
| Prompt templates (active) | Supabase `prompt_template` | Indefinite (operational) | Manual — only removed if feature discontinued |
| Prompt templates (inactive) | Supabase `prompt_template` | Indefinite (audit) | Never deleted — deactivated_at set |

---

### Biometric and Photo Data

| Data type | Location | Retention | Deletion mechanism |
|---|---|---|---|
| Original user photo | Railway memory | < 60 seconds | Deleted from memory after Fal.ai calls complete |
| Original user photo (Fal.ai) | Fal.ai infrastructure | Zero — per DPA | DPA prohibits retention |
| Generated future self image | Supabase Storage | Until user deletes or account deletion | User-initiated: Settings → Delete image. Account deletion: Storage bucket purge |
| BiometricConsent record | Supabase `biometric_consent` | 1 year after account deletion | `user_deleted_at` set at deletion time. APScheduler annual purge deletes rows where `user_deleted_at < NOW() - 1 year`. NOT cascade-deleted — `ON DELETE RESTRICT` on user FK. |

**Note on photo deletion verification:** An automated CI test (`@security` marker)
verifies the original photo is absent from all systems within 60 seconds of generation.
This test runs on every push to main.

---

### Operational Data

| Data type | Location | Retention | Deletion mechanism |
|---|---|---|---|
| Async job records | Supabase `job` | 7 days after completion | APScheduler nightly task: `DELETE WHERE completed_at < NOW() - 7 days` |
| Sync event log | Supabase `sync_event_log` | Until account deletion | CASCADE DELETE on `user` row |
| Support reports | Supabase `support_report` | 90 days | APScheduler monthly task |
| Push notification device tokens | Supabase `device_token` | Until de-registered or account deletion | De-registered on sign-out. APNs 410 response triggers deletion. CASCADE DELETE on account deletion. |
| Notification preferences | Supabase `user_notification_preference` | Until account deletion | CASCADE DELETE on `user` row |

---

### Analytics and Observability

| Data type | Location | Retention | Deletion mechanism |
|---|---|---|---|
| Crash reports | Sentry | 90 days | Sentry auto-deletion |
| Product analytics events | PostHog | Per PostHog plan | PostHog auto-deletion |
| Railway application logs | Railway | 7 days | Railway auto-deletion |
| Daily AI cost summary | Supabase `daily_ai_cost` | 12 months | APScheduler annual purge |

---

### Legal and Compliance Records

| Data type | Location | Retention | Deletion mechanism |
|---|---|---|---|
| BiometricConsent audit records | Supabase `biometric_consent` | 1 year after account deletion | `user_deleted_at` set at deletion time. APScheduler annual purge. ON DELETE RESTRICT — not cascade deleted. |
| Data subject requests log | Supabase `data_subject_requests` | 3 years | Manual review and purge on schedule |
| Incident log | `docs/INCIDENT_LOG.md` (git) | Indefinite | Never deleted |

**Note on BiometricConsent retention:** While most user data is deleted within 30 days
of an account deletion request, BiometricConsent records are retained for 1 additional
year as legal compliance evidence. This is disclosed in the Privacy Policy.

---

## Account Deletion Flow

When a user deletes their account:

1. **Immediate (on request):**
   - User signed out from all active sessions
   - Auth token invalidated
   - Account marked `pending_deletion`

2. **Within 24 hours (automated):**
   - All workout data deleted (CASCADE from `user` table)
   - All PersonalRecords deleted
   - All Jobs deleted
   - Sync event log deleted
   - Support reports deleted
   - Device tokens deleted
   - Future self image deleted from Supabase Storage
   - `user` row deleted

3. **Within 30 days (confirmed):**
   - Third-party processors notified where required by DPA
   - Deletion confirmed in `data_subject_requests` log

4. **Retained post-deletion:**
   - BiometricConsent record: 1 additional year
   - Anonymised analytics events (no user ID): indefinite

---

## Automated Deletion Tasks

All automated deletion is handled by APScheduler jobs in the FastAPI backend:

```python
# Runs nightly at 02:00 UTC
scheduler.add_job(purge_expired_ai_logs, "cron", hour=2, minute=0)
scheduler.add_job(purge_old_jobs, "cron", hour=2, minute=15)
scheduler.add_job(purge_old_support_reports, "cron", hour=2, minute=30)
```

Each task logs:
- How many rows were evaluated
- How many rows were deleted
- Any errors encountered

Logged at INFO level with `task_name`, `rows_evaluated`, `rows_deleted`.

---

## Data Subject Rights (GDPR Articles 17 and 20)

| Right | V1 mechanism | V2 mechanism |
|---|---|---|
| Right to erasure (Art. 17) | Account deletion in app → all data deleted within 30 days | Same |
| Right to access (Art. 20) | Email privacy@prlifts.app → manual export within 30 days | In-app data export |
| Right to portability (Art. 20) | Email privacy@prlifts.app → JSON export within 30 days | In-app download |

V1 stopgap: manual email process is acceptable for a small user base.
V2 requires in-app self-service before scaling.

