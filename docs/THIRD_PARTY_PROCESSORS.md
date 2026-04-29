# PRLifts — Third Party Data Processor Register

**Version:** 1.0
**Last updated:** April 2026
**Owner:** Privacy Counsel / DPO
**Audience:** Legal, Security, and all developers

> This register documents every external service that receives or processes
> user data. Required for GDPR Article 30 compliance. Updated whenever a
> new third-party integration is added. Never integrate a new service that
> handles user data without adding it to this register first.

---

## Register

### 1. Supabase (PostgreSQL + Auth + Storage)

| Field | Detail |
|---|---|
| **Purpose** | Primary database, authentication, and file storage |
| **Data received** | All user data: workout data, profile, biometric consent records, sync logs, support reports |
| **Data classification** | Personal + Sensitive |
| **Data center region** | US East (default) — verify in Supabase dashboard |
| **DPA status** | ✅ Supabase processes data under their DPA (accepted via Supabase terms) |
| **GDPR transfer mechanism** | Standard Contractual Clauses (SCCs) — Supabase's DPA covers EU-US transfers |
| **Privacy policy** | supabase.com/privacy |
| **Retention** | Until account deletion (30-day deletion window after request) |
| **Notes** | Supabase Storage holds generated future self images. Private buckets only. |

---

### 2. Railway

| Field | Detail |
|---|---|
| **Purpose** | API server hosting and deployment |
| **Data received** | Request/response logs (structured JSON, no PII), environment variables (contains API keys) |
| **Data classification** | Operational |
| **Data center region** | US West (Railway default) |
| **DPA status** | ✅ Railway DPA available and accepted |
| **GDPR transfer mechanism** | SCCs via Railway DPA |
| **Privacy policy** | railway.app/legal/privacy |
| **Retention** | Log retention: 7 days (configured). Environment variables: until deleted. |
| **Notes** | No user PII in Railway logs (enforced by logging standards). User photos are never written to Railway filesystem. |

---

### 3. Fal.ai

| Field | Detail |
|---|---|
| **Purpose** | AI image generation for the future self feature |
| **Data received** | User photo (biometric data), structured generation prompt (goal, gender) |
| **Data classification** | Biometric (highest sensitivity) |
| **Data center region** | Verify with Fal.ai before DPA execution |
| **DPA status** | ⚠️ MUST be executed before any photos are processed — see prerequisite |
| **GDPR transfer mechanism** | SCCs required if Fal.ai processes outside EU/EEA |
| **Privacy policy** | fal.ai/privacy (verify current URL) |
| **Retention** | Zero — DPA must prohibit any retention beyond the immediate request |
| **Notes** | This is the highest-risk processor in the system. Photos are biometric data under BIPA and GDPR Article 9. DPA execution is a hard prerequisite before the future_self feature is enabled. |

**Hard prerequisite:** Do not enable the `future_self_enabled` feature flag until:
1. Fal.ai DPA is signed and filed
2. Data center location confirmed
3. SCCs executed if required
4. DPA contains explicit prohibition on data retention beyond the request

---

### 4. Anthropic (Claude API)

| Field | Detail |
|---|---|
| **Purpose** | Text AI: workout insights, benchmarking feedback, quality gate scoring |
| **Data received** | Structured workout data (exercise names, weights, reps, user goal, gender) — no raw user text, no photos, no PII |
| **Data classification** | Personal (anonymised by design — no name/email in prompts) |
| **Data center region** | Anthropic US infrastructure |
| **DPA status** | ✅ Anthropic Enterprise DPA available. Standard API usage covered by Anthropic's terms. |
| **GDPR transfer mechanism** | SCCs via Anthropic's DPA or standard terms |
| **Privacy policy** | anthropic.com/privacy |
| **Retention** | Anthropic's standard API terms: prompts not used for training (verify current policy) |
| **Notes** | User-provided text (workout names, notes) is preprocessed and never sent directly to Claude. Structured data only. |

---

### 5. ExerciseDB / ASCEND API (via RapidAPI)

| Field | Detail |
|---|---|
| **Purpose** | Exercise library: exercise definitions, GIF demos, video URLs |
| **Data received** | No user data — read-only API calls for exercise catalogue |
| **Data classification** | None (no user data) |
| **DPA status** | N/A — no user data transmitted |
| **Notes** | Exercise data (including video URLs) is cached in Supabase after seeding. The `demo_url` field on the `exercise` table stores the EDB-provided video URL. Video content is served directly from EDB/RapidAPI CDN — PRLifts does not proxy or re-host video content. Ongoing API calls are for fresh data only, not user-specific queries. Using EDB v2 by ASCEND API (11,000+ exercises, includes videos/GIFs/images — Decision 76). |

---

### 6. Sentry

| Field | Detail |
|---|---|
| **Purpose** | Crash reporting and error tracking (iOS + backend) |
| **Data received** | Crash reports, stack traces, error events — PII stripped by scrubbing rules |
| **Data classification** | Operational (anonymised) |
| **Data center region** | US or EU (Sentry offers EU region — prefer EU for GDPR) |
| **DPA status** | ✅ Sentry DPA available |
| **GDPR transfer mechanism** | SCCs or EU data residency |
| **Privacy policy** | sentry.io/privacy |
| **Retention** | 90 days (Sentry default) |
| **Notes** | Scrubbing rules configured to strip email, display_name, auth tokens from all events. Verify scrubbing rules are active before launch. |

---

### 7. PostHog

| Field | Detail |
|---|---|
| **Purpose** | Product analytics and feature flags |
| **Data received** | Anonymous user events (anonymous UUID, event name, properties) — no PII |
| **Data classification** | Analytical (anonymised) |
| **Data center region** | EU or US (PostHog offers EU cloud — prefer EU) |
| **DPA status** | ✅ PostHog DPA available |
| **GDPR transfer mechanism** | EU data residency or SCCs |
| **Privacy policy** | posthog.com/privacy |
| **Retention** | Per PostHog plan |
| **Notes** | Anonymous user IDs only — no email, name, or PII in any event. Verify anonymous IDs are truly anonymous (not reversible to a user). |

---

### 8. Upstash Redis

| Field | Detail |
|---|---|
| **Purpose** | Rate limiting counter store |
| **Data received** | Rate limit counters keyed by anonymous user ID and endpoint — no user content |
| **Data classification** | Operational |
| **Data center region** | Matches Railway region (configure same region) |
| **DPA status** | ✅ Upstash DPA available |
| **Privacy policy** | upstash.com/trust/privacy |
| **Retention** | TTL-based — rate limit counters expire within minutes |
| **Notes** | No user content — only request counts. Very low privacy risk. |

---

### 9. Apple (APNs + Sign In with Apple)

| Field | Detail |
|---|---|
| **Purpose** | Push notifications and authentication |
| **Data received** | APNs: device tokens, notification payloads. Sign In: identity tokens. |
| **Data classification** | Operational |
| **DPA status** | Apple's Developer Program terms cover data processing |
| **Privacy policy** | apple.com/legal/privacy |
| **Notes** | Notification payloads contain no PII — device token only identifies the device. Apple's Sign In provides identity — Supabase Auth validates and we never store the raw Apple identity token. |

---

### 10. Google (Sign In with Google)

| Field | Detail |
|---|---|
| **Purpose** | Authentication via Google account |
| **Data received** | Identity token (OAuth) during sign-in flow |
| **Data classification** | Authentication |
| **DPA status** | Google Cloud DPA covers API usage |
| **Privacy policy** | policies.google.com/privacy |
| **Notes** | We receive and immediately validate the identity token via Supabase Auth. We do not store raw Google tokens. |

---

## Processor Review Schedule

This register must be reviewed and updated:
- Before any new third-party integration is added
- Annually (minimum)
- When a processor changes their privacy policy or data center location
- When GDPR, BIPA, or other regulations change in ways that affect processor requirements

---

## V2+ Planned Processors

| Service | Purpose | DPA required before use |
|---|---|---|
| Cloudflare R2 | Progress photo storage at scale | Yes |
| Stripe | Payment processing | Yes |
| Garmin Connect API | Wearable integration (V3) | Yes |
| Whoop API | Recovery data (V3) | Yes |
| Oura API | Sleep and recovery data (V3) | Yes |

