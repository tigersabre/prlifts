# PRLifts Privacy Policy — DRAFT

**Status:** DRAFT — requires attorney review before publication
**Last updated:** April 2026
**Effective date:** [To be set on publication]
**Contact:** privacy@prlifts.app

> ⚠ This is a working draft for attorney review.
> It must not be published as-is.
> Sections marked [ATTORNEY REVIEW] require specific legal input.

---

## Who We Are

PRLifts ("we", "us", "our") is a fitness tracking application. We are
the data controller for the personal information you provide to us.

Contact: privacy@prlifts.app

---

## What Information We Collect and Why

### Account Information

When you create an account, we collect:
- Email address (optional — not required if you sign in with Apple)
- Display name
- Date of birth (optional — collected in onboarding, used for benchmarking)
- Gender (optional — collected in onboarding, used for benchmarking)

**Why:** To create and maintain your account and to personalise your experience.

### Workout Data

When you log workouts, we collect:
- Exercise names and types
- Weights, reps, sets, duration, distance
- Rate of Perceived Exertion (RPE)
- Workout notes and names (optional)
- Workout dates and times

**Why:** To track your fitness progress and detect personal records.

### Fitness Goal

We collect your stated fitness goal (e.g., build muscle, improve endurance).

**Why:** To personalise the AI-generated coaching insights and the future
self image generation.

### Device and Technical Information

We collect:
- Device model and iOS version (for support and compatibility)
- App version
- Crash reports (anonymised, via Sentry)
- Anonymous usage events (via PostHog, identified by a random ID, not your email)

**Why:** To maintain and improve the app. Crash reports help us fix bugs.

---

## Photo Processing and AI-Generated Images

### How Your Photo Is Used

The "Future Self" feature allows you to submit a photo of yourself.
We use this photo to generate an AI image showing a healthier version of you.

**What happens to your original photo:**
1. Your photo is transmitted securely to our servers
2. Your photo is forwarded to our image generation partner (Fal.ai)
   for processing
3. Your original photo is permanently deleted from all our systems
   **within 60 seconds** of the generation being initiated
4. Fal.ai processes your photo under a Data Processing Agreement that
   prohibits them from retaining your photo

**What we keep:**
The AI-generated image is stored in your account and used in your
motivational notifications. You can delete it at any time in Settings.

**This is biometric data.** Under applicable laws including the Illinois
Biometric Information Privacy Act (BIPA) and GDPR Article 9, processing
biometric data requires explicit consent. We obtain this consent separately
before processing any photo.

### Explicit Consent Required

Before your photo is processed, you will see a clear, plain-language
consent screen explaining exactly what will happen. You can decline this
consent without affecting your use of any other PRLifts features.
You can revoke your consent and delete your generated image at any time
in Settings → Biometric Consent.

---

## AI-Generated Content

### Workout Insights

After your workouts, PRLifts generates brief, personalised coaching insights
using the Anthropic Claude AI. These insights are generated from:
- Your workout data (exercise names, weights, reps, dates)
- Your stated fitness goal

We do not send your name, email, or free-text notes to the AI provider.
Structured workout data only is sent.

### Benchmarking

If available, PRLifts can compare your personal records to general population
standards. This uses your exercise data, age (if provided), and gender
(if provided).

---

## Who We Share Your Data With

We use third-party services that process your data on our behalf.
We have Data Processing Agreements with all processors that handle
personal data. A full list of processors is available on request.

| Service | Purpose | Data shared |
|---|---|---|
| Supabase | Database and file storage | Your workout and account data |
| Railway | App server hosting | Request logs (anonymised) |
| Anthropic | AI text generation | Structured workout data (no name/email) |
| Fal.ai | AI image generation | Your photo (deleted within 60 seconds) |
| Sentry | Crash reporting | Anonymised crash data |
| PostHog | Product analytics and feature flags | Anonymous usage events |
| Apple APNs | Push notifications | Device token and notification content |

We do not sell your data. We do not share your data for advertising.

---

## Data Retention

| Data type | Retained until |
|---|---|
| Your account and workout data | Until you delete your account |
| Your generated future self image | Until you delete it or your account |
| Your original photo | Deleted within 60 seconds of processing |
| AI coaching logs (internal use) | 30 days |
| Biometric consent record | Until account deletion + 1 year [ATTORNEY REVIEW] |
| Anonymised crash reports (Sentry) | 90 days |

When you delete your account, your data is deleted within 30 days.

---

## Your Rights

### All Users

- **Delete your account:** Settings → Account → Delete Account
- **Delete your future self image:** Settings → Biometric Consent → Delete Image
- **Withdraw biometric consent:** Settings → Biometric Consent → Revoke Consent
- **Contact us:** privacy@prlifts.app for any data request

### EU/EEA Users (GDPR)

You have the right to:
- Access the personal data we hold about you
- Correct inaccurate data
- Delete your data (right to erasure)
- Receive your data in a portable format
- Object to processing
- Lodge a complaint with your data protection authority

To exercise any of these rights, contact privacy@prlifts.app.
We will respond within 30 days. [ATTORNEY REVIEW — confirm response timeframes]

### California Users (CCPA) [ATTORNEY REVIEW]

[ATTORNEY REVIEW: Confirm if CCPA applies at V1 launch scale.
If applicable, add CCPA rights section here.]

### Illinois Users (BIPA)

If you are an Illinois resident and use the Future Self feature:
- We collect your biometric data (facial geometry from photo processing)
- We have a written policy for retention and destruction (this document)
- Your original photo is destroyed within 60 seconds
- Your generated image is destroyed when you revoke consent or delete your account
- We do not sell or profit from your biometric data
- You may request destruction of your biometric data at any time

---

## Children's Privacy

PRLifts is not directed at children under 13. We do not knowingly collect
personal information from children under 13. If you believe a child has
provided us with personal information, contact privacy@prlifts.app.

[ATTORNEY REVIEW: Confirm age gate requirements for health app with AI image generation]

---

## Security

We protect your data using:
- Encryption in transit (TLS 1.3)
- Encryption at rest (Supabase + iOS Data Protection)
- Database-level access controls (Row Level Security)
- Certificate pinning on the iOS app
- Automated deletion of biometric data

No system is perfectly secure. If you discover a security vulnerability,
please report it to privacy@prlifts.app.

---

## Changes to This Policy

We will notify you of material changes to this policy through the app
or by email. Continued use after notification constitutes acceptance.

---

## Contact

Questions about this policy: privacy@prlifts.app

[ATTORNEY REVIEW: Confirm whether a physical address is required under
applicable laws for the data controller]

---

## Effective Date

This policy is effective as of [DATE TO BE SET ON PUBLICATION].

