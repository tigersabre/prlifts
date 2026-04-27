# PRLifts — User Flow Diagrams

**Version:** 1.0
**Last updated:** April 2026
**Owners:** Product Architect + UX Lead
**Audience:** All developers (human and Claude Code)

> Every major user flow is defined here: the happy path and the error paths.
> These are the specifications Claude Code builds UI against.
> Screen names match SCREEN_INVENTORY.md exactly.

---

## Flow 1 — First Launch and Phase 1 Onboarding

**Happy path:**

```
App first launch
  → WelcomeScreen
  → [Tap "Get Started"]
  → SignInScreen
  → [Sign in with Apple / Google / email]
      → Success → DisplayNameScreen
      → Failure → SignInScreen (error inline: "Sign in failed. Please try again.")
  → DisplayNameScreen
  → [Enter display name, tap Continue]
      → Valid → UnitPreferenceScreen
      → Invalid (empty) → inline error: "Please enter a display name"
  → UnitPreferenceScreen
  → [Select units, tap Continue]
  → HomeScreen (Phase 1 complete)
```

**Key rules:**
- Phase 1 cannot be skipped or exited without completing all 4 steps
- Returning user on subsequent launches: if auth token valid → HomeScreen directly
- Returning user with expired token → SignInScreen (not WelcomeScreen)
- Network unavailable during sign in → inline error, retry button

---

## Flow 2 — Logging a Workout (Core Flow)

**Happy path:**

```
HomeScreen
  → [Tap "Start workout"]
  → ActiveWorkoutScreen (new workout created, status: in_progress)
  → [Tap "Add exercise"]
      → ExerciseLibraryScreen (modal)
      → [Search or browse, tap exercise]
      → ExerciseLibraryScreen dismissed, exercise added to workout
  → [Log sets for each exercise]
      → [Tap set row to log weight/reps/RPE]
      → [Tap "Log set"]
          → Online: Set saved locally + synced immediately
              → If PR detected: PRNotificationBanner appears inline
          → Offline: Set saved locally, queued for sync
  → [Tap "Finish workout"]
      → WorkoutCompleteScreen
          → PR summary shown (if any PRs)
          → AI insight polling begins
              → Insight appears when job completes (progressive messaging)
              → If insight times out: "Insight unavailable. Try again later."
  → [Tap "Done"]
  → HomeScreen
      → If Phase 2 not completed: Phase 2 prompt appears (see Flow 3)
```

**Error paths:**
- Exercise search returns no results → empty state with "Create custom exercise" CTA
- Set logged with neither weight, reps, nor duration → inline validation error
- Workout abandoned (app force-quit) → workout remains `in_progress`
  → on next launch: "You have an unfinished workout. Continue or discard?"

**Offline behaviour:**
- OfflineBannerComponent shown persistently
- All set logging works normally (SwiftData)
- Sync icon shows pending count
- On reconnect: silent background sync, banner disappears

---

## Flow 3 — Phase 2 Onboarding (Post-First-Workout)

**Trigger:** User completes their first workout and taps "Done" on WorkoutCompleteScreen.

**Happy path (full):**

```
WorkoutCompleteScreen → [Tap "Done"]
  → GoalSelectionScreen
  → [Select goal, tap Continue]  OR  [Tap Skip]
  → DemographicsScreen
  → [Enter optional details, tap Continue]  OR  [Tap Skip]
  → BiometricConsentScreen
  → [Read full consent text]
      → [Tap "Agree"]
          → BiometricConsent record written to backend
              → Success → PhotoCaptureScreen
              → Failure → Error message: "Something went wrong saving your consent.
                          Please try again."
                          [Retry button]  —  photo NOT processed
      → [Tap "No thanks"]
          → Skip to NotificationPermissionScreen
  → PhotoCaptureScreen
  → [Take photo or upload]
      → Photo submitted → future_self job created (job_id returned)
      → FutureSelfRevealScreen (polling begins)
          → Polling messages: "Analyzing your photo..." →
            "Building your future self..." → "Almost ready..."
          → On success:
              → Content warning shown briefly
              → Image revealed
              → Celebration state (one emoji permitted)
              → [Tap Continue]
          → On quality gate failure or job expiry:
              → "Your vision is being crafted — check back soon"
              → [Tap Continue]
  → NotificationPermissionScreen
  → [Tap "Allow Notifications"] → iOS permission dialog
      → Granted → device token registered to backend
      → Denied → continue (user can enable later in Settings)
  → HomeScreen (Phase 2 complete)
```

**Skip variations:**

| User choice | What happens |
|---|---|
| Skip GoalSelection | goal = null on User; Phase 2 continues |
| Skip Demographics | date_of_birth + gender remain default; Phase 2 continues |
| Decline BiometricConsent | future_self feature disabled; skip to NotificationPermissionScreen |
| Skip PhotoCapture | future_self feature inactive; skip to NotificationPermissionScreen |
| Deny notifications | notifications not sent; user can enable in Settings later |

**Re-entry:** If user exits the app mid-Phase 2, they resume where they left off
on next launch — Phase 2 state is tracked on the User record.

---

## Flow 4 — Future Self Regeneration

**Trigger:** User taps "Regenerate" on FutureSelfScreen.

```
FutureSelfScreen
  → [Tap "Regenerate image"]
      → Check monthly limit (5/month)
          → At limit: "You've used all your image generations this month.
                      Come back in [X days]."
          → Under limit → PhotoCaptureScreen (same flow as Phase 2)
  → PhotoCaptureScreen
  → [Take or upload new photo]
  → FutureSelfRevealScreen (same polling + reveal flow)
  → On success: new image replaces old image in FutureSelfScreen
  → On failure: existing image shown, warm message: "We couldn't generate a new
                image this time. Your previous image is still here."
```

---

## Flow 5 — Personal Record Achieved (In-Workout)

**Trigger:** WorkoutSet logged with `is_completed = true` triggers PR detection.

```
ActiveWorkoutScreen
  → [User taps "Log set"]
  → Set saved + PR detection runs
  → If PR detected:
      → PRNotificationBanner appears inline above the set input area
          → Banner content: exercise name, new value, improvement delta
          → [User taps banner] → PersonalRecordDetailScreen (modal)
          → [User swipes banner away] → banner dismissed, workout continues
      → If notifications permitted: `pr_achieved` notification queued
  → Workout continues
```

---

## Flow 6 — Push Notification Handling

**PR Achieved notification tapped:**

```
User taps PR notification
  → App opens / foregrounds
  → Deep link resolved: /records/detail/{record_id}
  → PersonalRecordDetailScreen presented
```

**Workout Reminder tapped:**

```
User taps workout reminder
  → App opens / foregrounds
  → Deep link resolved: /workout/start
  → ActiveWorkoutScreen (new workout created immediately)
```

**Show-up Nudge tapped:**

```
User taps show-up nudge
  → App opens / foregrounds
  → Deep link resolved: /future-self (if image available)
                         /home (if no image)
  → FutureSelfScreen or HomeScreen
```

---

## Flow 7 — Account Deletion

**Happy path:**

```
SettingsScreen
  → [Tap "Delete account"]
  → DeleteAccountScreen
  → "To confirm, type DELETE below"
  → [User types "DELETE"]
  → [Tap "Delete my account"]
      → Confirmation dialog: "This is permanent. All your data will be deleted."
      → [Tap "Delete permanently"]
          → Account deletion initiated
          → User signed out immediately
          → App returns to WelcomeScreen (fresh state)
          → Data deletion completes within 30 days (backend job)
      → [Tap "Cancel"] → returns to DeleteAccountScreen
```

---

## Flow 8 — Offline Sync Recovery

**Trigger:** User force-quits app mid-workout. Restarts app.

```
App launch
  → SwiftData loaded
  → SyncEventLog checked for uploaded_at = null entries
  → If pending entries found:
      → Background sync queued immediately
      → Sync runs before UI is interactive (blocking for < 2 seconds)
      → If sync fails: continues to app, retry on next foreground or connectivity event
  → App continues normally
  → No user-facing prompt unless sync consistently fails (> 3 attempts)
      → If 3 consecutive failures: subtle banner: "Some data may not be saved.
                                   Tap to report a problem."
```

---

## Flow 9 — Reporting a Problem

```
SettingsScreen OR persistent failure banner
  → [Tap "Report a problem"]
  → System prompt (dialog):
      → "Can we include recent sync data to help diagnose the problem?
         This helps us identify what went wrong."
      → [Include sync data] → uploads SyncEventLog entries → opens report form
      → [Just report] → opens report form without sync data
  → Report form (in-app text field)
  → [Tap "Submit"]
  → SupportReport created in backend
  → "Thanks for reporting. We'll look into it."
```

