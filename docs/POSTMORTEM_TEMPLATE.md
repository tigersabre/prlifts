# PRLifts — Post-Mortem Template

**Owner:** DevOps Lead
**Audience:** All developers

> Copy this template for every P1 and P2 incident.
> Post-mortems are learning documents — not blame documents.
> The goal is to understand what happened and prevent recurrence.
> Complete within 48 hours of incident resolution.

---

# Post-Mortem: [Short Title]

**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P1 / P2
**Author:** [Name]
**Reviewers:** [Names]

---

## Summary

One paragraph. What happened, who was affected, how it was resolved.
Write this last — after completing the rest of the document.

---

## Timeline

| Time (UTC) | Event |
|---|---|
| HH:MM | First alert / user report |
| HH:MM | Developer notified |
| HH:MM | Investigation started |
| HH:MM | Root cause identified |
| HH:MM | Fix deployed |
| HH:MM | Service restored |
| HH:MM | All-clear declared |

---

## Root Cause

What was the actual cause? Be specific. "Database was slow" is not a root
cause. "Missing index on workout_set caused full table scan on every PR
detection call, causing timeouts under concurrent load" is a root cause.

---

## Contributing Factors

What conditions allowed the root cause to cause an incident?
Examples:
- No alerting on query latency
- Test suite did not cover this code path under load
- Deployment did not verify health check after deploy

---

## User Impact

- How many users were affected?
- What could they not do?
- Were any users' data affected?
- Did any user data need to be restored?

---

## Detection

- How was the incident detected? (Sentry alert / user report / developer noticed)
- How long was the incident occurring before detection?
- What would have detected it faster?

---

## Resolution

What steps were taken to resolve the incident?

---

## What Went Well

Even in bad incidents, something goes right. Note it here.
Examples: escalation was fast, runbook covered this scenario, rollback worked.

---

## Action Items

Concrete tasks to prevent recurrence. Each has an owner and a due date.

| Action | Owner | Due date | GitHub issue |
|---|---|---|---|
| Add query latency alerting | DevOps | YYYY-MM-DD | #123 |
| Add test for high-concurrency PR detection | QA | YYYY-MM-DD | #124 |
| Add missing index to SCHEMA.md | Data | YYYY-MM-DD | #125 |

---

## Lessons Learned

What would you do differently next time? What does this incident teach us
about the system, the process, or the team?

