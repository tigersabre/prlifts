# PRLifts — Threat Model

**Version:** 1.0
**Last updated:** April 2026
**Owner:** Security Architect
**Audience:** All developers (human and Claude Code)

> This document maps every attack surface, the realistic threat actors,
> and the mitigations in place. It is used to verify that security controls
> are correctly implemented and to guide security review during code review.
> STRIDE methodology is applied throughout.

---

## STRIDE Reference

| Letter | Threat | Question |
|---|---|---|
| S | Spoofing | Can an attacker pretend to be someone else? |
| T | Tampering | Can an attacker modify data in transit or at rest? |
| R | Repudiation | Can an actor deny having taken an action? |
| I | Information Disclosure | Can an attacker read data they should not? |
| D | Denial of Service | Can an attacker make the service unavailable? |
| E | Elevation of Privilege | Can an attacker gain more access than allowed? |

---

## Threat Actors

| Actor | Motivation | Technical capability |
|---|---|---|
| Casual attacker | Curiosity, opportunism | Low — uses known exploits and tooling |
| Credential thief | Access to user accounts | Medium — phishing, credential stuffing |
| Data harvester | Bulk user data exfiltration | Medium-high — API abuse, SQL injection |
| Malicious insider | Access to admin systems | High — knows the system |
| Automated scanner | Vulnerability discovery | Medium — uses OWASP scanners |

---

## Attack Surface 1 — iOS App

### S1.1 — Authentication Spoofing

**Threat (S):** Attacker presents a forged or stolen JWT to access another user's data.
**Mitigations:**
- Supabase JWT verified on every request (signature + expiry)
- Short-lived tokens with automatic refresh
- RLS enforces `user_id = auth.uid()` at the database level — even a valid token cannot read another user's data

**Residual risk:** Low. RLS is the defence-in-depth that catches application-layer auth bypasses.

---

### S1.2 — Sign-In Provider Spoofing

**Threat (S):** Attacker crafts a fake Apple or Google identity token.
**Mitigations:**
- Identity tokens validated directly with Apple/Google servers by Supabase Auth
- App never trusts client-provided identity claims

**Residual risk:** Very low.

---

### T1.3 — Network Interception (Gym WiFi)

**Threat (T/I):** Attacker on the same network intercepts requests, including photo uploads for the future self feature.
**Mitigations:**
- TLS 1.3 enforced — no HTTP fallback
- TrustKit SSL certificate pinning on iOS for the backend connection (CA-level, with backup pin)
- Photo transmitted directly to backend — never written to a shared location

**Residual risk:** Low. Certificate pinning prevents MITM on iOS. Pinning rotation documented in RUNBOOK.md.

---

### T1.4 — Token Storage Tampering

**Threat (T):** Attacker with local device access reads auth tokens from storage.
**Mitigations:**
- Auth tokens stored exclusively in iOS Keychain with appropriate protection class
- Keychain data encrypted by iOS Data Protection
- Tokens never stored in UserDefaults, NSCache, or app files

**Residual risk:** Low on locked devices. Physical access to an unlocked device is out of scope.

---

### I1.5 — Sensitive Data in Logs

**Threat (I):** Crash reports or logs expose PII or auth tokens.
**Mitigations:**
- Sentry scrubbing rules strip email, display name, auth tokens from crash reports
- No PII in any log statements (enforced by Security coding standards + CI secret scanning)
- Photo content never logged — only metadata (job_id, duration_ms)

**Residual risk:** Low. Developers must never log PII — enforced by code review and linting.

---

## Attack Surface 2 — Backend API

### T2.1 — SQL Injection

**Threat (T/I):** Attacker injects SQL through API parameters to read or modify data.
**Mitigations:**
- All database queries use SQLAlchemy ORM with parameterized queries
- Raw SQL is prohibited (STANDARDS.md — blocking PR review issue)
- Input validation via Pydantic schemas with explicit bounds on every field
- Ruff linter flags dangerous string formatting patterns

**Residual risk:** Very low. Multiple independent layers prevent injection.

---

### T2.2 — Mass Assignment

**Threat (T/E):** Attacker sends extra fields in API payloads to set values they should not control (e.g., `beta_tier`, `user_id`).
**Mitigations:**
- Pydantic request models explicitly define allowed fields — extra fields are rejected
- FastAPI's `model_config = ConfigDict(extra='forbid')` configured on all request models
- `user_id` is always taken from the verified JWT — never from the request body

**Residual risk:** Very low.

---

### D2.3 — Rate Limit Exhaustion

**Threat (D):** Attacker floods the API to cause service degradation or exhaust AI API credits.
**Mitigations:**
- Per-user rate limits enforced via Upstash Redis middleware
- AI endpoints limited to 10 req/min/user (combined Claude + Fal.ai)
- Auth endpoints limited to 5 attempts/min/IP
- Monthly AI usage limits per user (60 insights, 5 image regenerations)
- Circuit breaker auto-disables AI features if daily spend threshold exceeded

**Residual risk:** Medium for motivated attackers with many accounts. V2 mitigation: stricter account verification.

---

### I2.4 — Insecure Direct Object Reference (IDOR)

**Threat (I):** Attacker guesses or enumerates workout IDs to read another user's data.
**Mitigations:**
- All IDs are UUIDs (not sequential integers — not guessable)
- RLS enforces ownership at the database level on every table
- Application-level ownership check in service layer (defence-in-depth)
- `workout_not_owned` error returned without confirming the resource exists (prevents enumeration)

**Residual risk:** Very low.

---

### T2.5 — Biometric Data Exfiltration

**Threat (T/I):** Attacker intercepts or retains user photos during the future self generation flow.
**Mitigations:**
- Photo held in memory only — never written to Railway filesystem
- Forwarded to Fal.ai over TLS immediately after receipt
- Deleted from memory within 60 seconds (automated CI test verifies)
- Fal.ai DPA prohibits retention beyond the immediate request
- No photo content in any log — only metadata
- BiometricConsent required before any photo accepted

**Residual risk:** Low. Primary residual risk is Fal.ai's own security posture — mitigated by DPA.

---

### E2.6 — Biometric Consent Bypass

**Threat (E):** Attacker submits a photo for future self generation without BiometricConsent.
**Mitigations:**
- Backend verifies BiometricConsent exists and `consent_given = true` before accepting any photo
- BiometricConsent is backend-write-only (no client writes via RLS)
- If consent write fails for any reason, photo is rejected immediately — not accepted
- This verification is the first action in the future_self job handler

**Residual risk:** Very low.

---

### I2.7 — AI Prompt Injection

**Threat (I):** Attacker crafts workout names or notes that manipulate the AI prompt to extract data or generate harmful content.
**Mitigations:**
- User-provided text (workout names, notes) is never interpolated directly into AI prompts
- A safe preprocessing step summarises user text before inclusion
- Prompt templates include explicit constraints on what the model must not output
- AI responses validated against forbidden phrases list before display

**Residual risk:** Low for data exfiltration. Medium for content quality manipulation — mitigated by response validation.

---

### T2.8 — Job Manipulation

**Threat (T):** Attacker creates jobs on behalf of another user, or polls another user's jobs.
**Mitigations:**
- Job creation uses `user_id` from JWT — never from request body
- Job polling endpoint verifies job belongs to the authenticated user
- RLS on Job table: `user_id = auth.uid()` for SELECT

**Residual risk:** Very low.

---

## Attack Surface 3 — Admin and Infrastructure

### I3.1 — API Key Exposure

**Threat (I):** API keys (Claude, Fal.ai, Supabase) are exposed in logs, code, or version control.
**Mitigations:**
- All secrets stored in Railway environment variables — never in code
- Secret scanning runs in CI on every push (blocks merge on finding secrets in code)
- Pre-commit hooks check for common secret patterns
- `.env` files are in `.gitignore` and their format is documented in `.env.example`
- Pre-launch secrets audit before first public build

**Residual risk:** Low. Primary risk is developer error — mitigated by automated scanning.

---

### I3.2 — AI Request Log Exposure

**Threat (I):** AI request logs (containing AI prompts and responses) are accessed by unauthorised parties.
**Mitigations:**
- `ai_request_log` table has no RLS policy accessible to client-facing APIs
- Access requires service role key — not available to the iOS app or regular API requests
- 30-day retention with automated deletion
- Table not included in any user-facing data export

**Residual risk:** Very low.

---

### D3.3 — Database Connection Pool Exhaustion

**Threat (D):** Attacker opens many connections to exhaust the Supabase connection pool (60 connections on free tier).
**Mitigations:**
- PgBouncer (Supabase built-in) manages connection pooling
- SQLAlchemy connection pool configured with explicit limits
- Rate limiting reduces concurrent connection creation from the API

**Residual risk:** Medium on free tier. Resolved by Supabase Pro upgrade before public launch.

---

## Controls Not Yet Implemented (V2)

| Threat | Mitigation planned |
|---|---|
| Credential stuffing at scale | CAPTCHA or account lockout on auth endpoint |
| Scraped user data correlation | More restrictive data export policy |
| Penetration testing | Third-party pen test before V2 launch |
| Bug bounty | V2+ after security posture is mature |

---

## Security Review Checklist (Per Feature)

When any feature touches user data or external services, verify:

- [ ] New endpoints have rate limiting applied
- [ ] All inputs validated with explicit bounds
- [ ] User ID taken from JWT, never from request body
- [ ] New tables have RLS policies before first data write
- [ ] No PII in any log statement
- [ ] Error messages contain no internal detail
- [ ] Any new third-party integration has a DPA in place

