# PRLifts — App Store Submission Checklist

**Version:** 1.0
**Last updated:** April 2026
**Owners:** iOS Platform Lead + Privacy Counsel
**Audience:** Developer submitting to App Store

> Complete every item before submitting for App Store review.
> Items marked ⚠ have failed App Store reviews for other apps —
> pay extra attention to these.

---

## Phase 1 — Legal and Compliance (Complete Before Any Build)

- [ ] Privacy Policy published at a stable URL (not localhost)
- [ ] Privacy Policy covers: photo processing, AI-generated images,
      biometric data, third-party processors, GDPR rights, CCPA
- [ ] Privacy Policy attorney-reviewed
- [ ] Terms of Service published
- [ ] Health disclaimer included in onboarding (not just in ToS)
- [ ] Biometric consent flow reviewed by attorney
- [ ] Fal.ai DPA executed (required before `future_self_enabled`)
- [ ] USPTO trademark application filed (Class 9 + Class 41)
- [ ] `prlifts.app` domain registered
- [ ] `prlifts.com` domain registered

---

## Phase 2 — Technical Pre-Launch (Complete Before TestFlight External)

- [ ] All CI gates passing on main branch
- [ ] Test coverage ≥ 90% (iOS + backend)
- [ ] Security test plan completed (SECURITY_TEST_PLAN.md)
- [ ] OWASP Mobile Top 10 checklist signed off
- [ ] Photo deletion CI test (`@security`) passing
- [ ] Secrets audit complete — no secrets in code or git history
- [ ] TrustKit certificate pinning verified with real device
- [ ] Deep links tested on physical device (not just simulator)
- [ ] Push notifications tested on physical device
- [ ] Supabase upgraded to Pro (7-day backup retention)
- [ ] Railway always-on enabled (no cold starts in production)
- [ ] Sentry SMS alerting configured for P1 events
- [ ] Backup restore tested at least once

---

## Phase 3 — App Store Connect Setup

### App Information

- [ ] App name: **PRLifts** (verify trademark clear)
- [ ] Subtitle: (e.g., "Workout Tracker + AI Coach") — 30 chars max
- [ ] Bundle ID: `app.prlifts`
- [ ] SKU: unique identifier for your records
- [ ] Category: **Health & Fitness** (primary)
- [ ] Secondary category: **Sports** (optional)
- [ ] Age rating: **4+** (no mature content, verify with AI content in review notes)
- [ ] Content rights: confirm you own all content
- [ ] Price: Free

### Privacy Nutrition Labels

Complete the App Privacy section in App Store Connect. PRLifts must declare:

| Data type | Collected | Linked to user | Used for tracking |
|---|---|---|---|
| Health and fitness (workout data) | Yes | Yes | No |
| User content (workout notes, exercise names) | Yes | Yes | No |
| Identifiers (user ID) | Yes | Yes | No |
| Usage data (feature analytics via PostHog) | Yes | No (anonymous) | No |
| Diagnostics (crash reports via Sentry) | Yes | No | No |
| Sensitive info (biometric data — photos) | Yes | Yes | No |

⚠ **Photos are biometric data** — declare them as sensitive information.
Explain in review notes that photos are processed and deleted within 60 seconds.

---

## Phase 4 — Screenshots and Metadata

### Screenshots Required

| Device | Count |
|---|---|
| iPhone 6.9" (iPhone 16 Pro Max) | 3–10 screenshots |
| iPhone 6.7" (iPhone 15 Plus) | 3–10 screenshots (or use 6.9" if identical) |
| iPad Pro 13" M4 | 3–10 screenshots (if iPad supported) |

**Screenshot content:**
- [ ] HomeScreen showing workout stats and streak
- [ ] ActiveWorkoutScreen logging a set with PR banner
- [ ] WorkoutCompleteScreen with AI insight visible
- [ ] FutureSelfRevealScreen (future self image blurred/placeholder in screenshots — see review notes)
- [ ] PRHistoryScreen showing progression

⚠ **Do not show real user faces** in screenshots — use clearly synthetic test data.

### App Description

- [ ] Short description (< 170 chars, shown in search results)
- [ ] Long description (< 4000 chars)
- [ ] Keywords (< 100 chars, comma-separated — research before finalising)
- [ ] What's New text for first version: "Initial release"
- [ ] Support URL: your support page or email
- [ ] Marketing URL: `https://prlifts.app`
- [ ] Privacy Policy URL: URL to published privacy policy

---

## Phase 5 — App Review Notes (Critical)

⚠ The AI image generation feature WILL trigger questions from App Review.
Prepare detailed review notes before submission.

### Review Notes Template

```
PRLifts Review Notes

DEMO ACCOUNT
Email: reviewer@prlifts.app
Password: ReviewPRLifts2026!
(Account pre-loaded with workout history and AI features enabled)

AI-GENERATED IMAGES — IMPORTANT
PRLifts includes a "Future Self" feature that generates an AI image of
the user looking fit. This feature:

1. Requires explicit biometric consent before any photo is processed
2. Processes photos through Fal.ai (third-party AI image generation)
3. Deletes the original photo from all systems within 60 seconds
4. Shows a content warning before revealing the generated image
5. Allows users to delete their generated image at any time in Settings

The feature complies with BIPA and GDPR requirements for biometric
data processing. Our Privacy Policy (linked above) explicitly discloses
this processing.

The AI-generated images are produced to encourage users to maintain
their fitness goals. Images show the user in a healthier physical state —
not weight loss or dangerous body modification. The system prompt
explicitly prohibits generating images targeting weight loss.

PUSH NOTIFICATIONS
Three notification types are used:
1. PR achieved — fires when the user sets a new personal record (content, not marketing)
2. Workout reminder — user-configured schedule (opted in explicitly)
3. Show-up nudge — motivational nudge on workout days (opted in explicitly)

All notification permissions are requested in context, not on first launch.

HEALTH DISCLAIMER
A health disclaimer is shown during onboarding (Step 4 of Phase 2):
"PRLifts provides fitness tracking and AI-generated coaching. It is not
a substitute for professional medical advice."

BACKGROUND CAPABILITIES
Background App Refresh: used for offline workout data sync only.
No persistent background execution.
```

---

## Phase 6 — Final Submission Checklist

- [ ] Build uploaded via Xcode or Transporter
- [ ] Version number and build number correct
- [ ] All screenshots uploaded for required device sizes
- [ ] App description and metadata complete
- [ ] Privacy nutrition labels complete
- [ ] Review notes written (use template above)
- [ ] Demo account credentials in review notes
- [ ] Privacy Policy URL valid and accessible
- [ ] Support URL valid and accessible
- [ ] Compliance declarations complete
- [ ] Export compliance: answer "No" to encryption questions (uses standard iOS/TLS)

---

## Common Rejection Reasons and Mitigations

| Rejection reason | Our mitigation |
|---|---|
| 5.1.1 — Privacy: data collection not disclosed | Privacy nutrition labels + privacy policy |
| 5.1.2 — Privacy: biometric data | Explicit consent flow + data deletion + review notes |
| 4.0 — Design: minimal functionality | Workout logging + AI features + PR tracking is core functionality |
| 2.1 — Performance: crashes | 90% test coverage + crash-free session target |
| 3.1.1 — Payments: features behind paywall not disclosed | All features free in V1 — no paywall disclosure needed |

