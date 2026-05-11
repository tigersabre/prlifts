# PRLifts — Screen Inventory

**Version:** 1.0
**Last updated:** April 2026
**Owners:** iOS Platform Lead + Product Architect
**Audience:** All developers (human and Claude Code)

> Every screen in the app is listed here with its name, route, required data,
> and supported actions. Screen names in this document are the canonical names
> used in code, navigation, analytics, and documentation.
> If you add a screen, add it here first.

---

## Naming Convention

Screen names use PascalCase. Route identifiers use kebab-case.
Analytics event names use snake_case prefixed with `screen_`:
`WorkoutHistory` → `/workout/history` → `screen_workout_history`

---

## Phase 1 Onboarding Screens

### WelcomeScreen
- **Route:** `/onboarding/welcome`
- **Analytics:** `screen_onboarding_welcome`
- **Required data:** None
- **Actions:** Begin onboarding (→ SignInScreen)
- **Notes:** First screen on fresh install. Not shown on subsequent launches.

### SignInScreen
- **Route:** `/onboarding/sign-in`
- **Analytics:** `screen_onboarding_sign_in`
- **Required data:** None
- **Actions:** Sign in with Apple, Sign in with Google, Sign in with email
- **Notes:** Handles both new account creation and returning user sign-in.
  Error states: invalid credentials, network unavailable, Apple/Google auth failure.

### DisplayNameScreen
- **Route:** `/onboarding/display-name`
- **Analytics:** `screen_onboarding_display_name`
- **Required data:** None (prefills from auth provider if available)
- **Actions:** Set display name, continue
- **Notes:** Minimum 1 character, maximum 50 characters.

### UnitPreferenceScreen
- **Route:** `/onboarding/units`
- **Analytics:** `screen_onboarding_units`
- **Required data:** None
- **Actions:** Select kg or lbs, select cm or inches, continue
- **Notes:** Defaults to lbs/inches for US locale, kg/cm for all others.
  Detected from device locale — user can override.

---

## Phase 2 Onboarding Screens (Post-First-Workout)

### GoalSelectionScreen
- **Route:** `/onboarding/goal`
- **Analytics:** `screen_onboarding_goal`
- **Required data:** None
- **Actions:** Select goal (build_muscle | lose_fat | improve_endurance |
  athletic_performance | general_fitness), continue, skip
- **Notes:** Skippable. If skipped, `goal` remains null on User.
  Future self feature requires a goal — user prompted again if they
  attempt the feature without a goal.

### DemographicsScreen
- **Route:** `/onboarding/demographics`
- **Analytics:** `screen_onboarding_demographics`
- **Required data:** None
- **Actions:** Set date of birth, set gender (male | female | na), continue, skip
- **Notes:** Fully skippable. Both fields optional.

### BiometricConsentScreen
- **Route:** `/onboarding/biometric-consent`
- **Analytics:** `screen_onboarding_biometric_consent`
- **Required data:** Current biometric consent policy version and text
- **Actions:** Agree (creates BiometricConsent record → PhotoCaptureScreen),
  Decline (skips future self feature entirely)
- **Notes:** Shown only if user has not previously consented.
  Consent text displayed in full — no "see full policy" link.
  Declining skips PhotoCaptureScreen and FutureSelfRevealScreen.
  User can revisit in Settings.

### PhotoCaptureScreen
- **Route:** `/onboarding/photo-capture`
- **Analytics:** `screen_onboarding_photo_capture`
- **Required data:** BiometricConsent record (must exist and be accepted)
- **Actions:** Take photo with camera, upload from library, continue (triggers
  async Job of type `future_self`), skip
- **Notes:** Only reachable with confirmed BiometricConsent.
  Photo is processed immediately — user does not wait on this screen.
  Job runs in background. User continues to FutureSelfRevealScreen
  which polls for the result.

### FutureSelfRevealScreen
- **Route:** `/onboarding/future-self`
- **Analytics:** `screen_onboarding_future_self`
- **Required data:** Job ID (from photo submission)
- **Actions:** View generated image, save to camera roll (optional), continue
- **Notes:** Polls Job status with exponential backoff.
  Shows progressive messaging during polling.
  On quality gate failure or job expiry: shows warm fallback message.
  On success: content warning shown before image reveal.
  Celebrate with defined celebration state (one emoji permitted).

### NotificationPermissionScreen
- **Route:** `/onboarding/notifications`
- **Analytics:** `screen_onboarding_notifications`
- **Required data:** Future self image URL (if generated) for context display
- **Actions:** Allow notifications, skip
- **Notes:** Shown after FutureSelfRevealScreen (or after DemographicsScreen
  if user skipped photo capture). Shows future self image if available
  to provide visual context for the notification value proposition.

---

## Main App Screens

### HomeScreen
- **Route:** `/home`
- **Analytics:** `screen_home`
- **Required data:** User profile, most recent workout summary,
  workouts logged this week, personal weekly average, best week (lifetime),
  next scheduled workout (if plan active)
- **Actions:** Start ad hoc workout (→ ActiveWorkoutScreen),
  start planned workout (→ ActiveWorkoutScreen),
  view future self (→ FutureSelfScreen),
  navigate to history, exercises, profile
- **Notes:** Primary landing screen after onboarding and on subsequent launches.
  Weekly Consistency card — shows workouts logged this week vs personal weekly average
  (e.g., 3 of 4), 7-day progress bar, Best Week stat showing personal record for
  workouts in a single week. See ARCHITECTURE.md Decision 92.

### ActiveWorkoutScreen
- **Route:** `/workout/active`
- **Analytics:** `screen_active_workout`
- **Required data:** Workout (in_progress or paused), WorkoutExercises,
  WorkoutSets, Exercise library for adding exercises
- **Actions:** Add exercise, log set, complete set, complete workout,
  pause workout, abandon workout (→ partial_completion),
  view exercise demo, reorder exercises, delete exercise
- **Notes:** Offline-capable — all writes go to SwiftData first.
  Timer display for rest periods (optional).
  PR detection runs after each set completion.
  PRNotificationBanner shown inline when PR detected.

### PRNotificationBanner
- **Route:** N/A (inline component on ActiveWorkoutScreen)
- **Analytics:** `component_pr_banner_shown`, `component_pr_banner_tapped`
- **Required data:** PersonalRecord, Exercise name, previous value
- **Actions:** Tap to expand detail (→ PersonalRecordDetailScreen)
- **Notes:** Not a full screen. Displayed inline above the set logging area.

### EditSetSheet
- **Route:** N/A (inline bottom sheet on ActiveWorkoutScreen and WorkoutDetailScreen)
- **Analytics:** `sheet_edit_set_opened`, `sheet_edit_set_saved`, `sheet_edit_set_cancelled`,
  `sheet_edit_set_deleted`
- **Required data:** WorkoutSet (reps, weight, weight_modifier, notes), PR status of this set
- **Actions:** Edit reps, weight, weight_modifier, notes; save (triggers PR recalculation);
  cancel; delete set (with confirmation alert on the sheet)
- **Notes:** Not a full screen. Presented as a bottom sheet over the calling screen.
  **PR warning:** If the set being edited is the basis for a PersonalRecord, a warning
  appears inline when the sheet opens — before any edits are made, not after save.
  Warning copy: "This set is a personal record. Editing or deleting it may update
  your records."
  **Delete:** Available directly on this sheet (not a separate screen). Tapping Delete
  shows a confirmation alert: "Delete this set? Your personal records may be updated."
  Confirmed delete triggers PR recalculation across all historical sets (Decision 87).

### WorkoutCompleteScreen
- **Route:** `/workout/complete`
- **Analytics:** `screen_workout_complete`
- **Required data:** Completed Workout, all WorkoutSets, PRs detected,
  AI insight Job ID
- **Actions:** View PR details, view AI insight (polls Job),
  share workout (V4), done (→ HomeScreen)
- **Notes:** AI insight displayed when Job completes.
  Uses progressive messaging while polling.
  PR achievements shown with celebration state.

### WorkoutHistoryScreen
- **Route:** `/workout/history`
- **Analytics:** `screen_workout_history`
- **Required data:** Paginated list of Workouts for current user,
  ordered by started_at descending
- **Actions:** Tap workout (→ WorkoutDetailScreen), filter by format,
  filter by date range, search
- **Notes:** Empty state: "No workouts yet" + "Log your first workout" button.

### WorkoutDetailScreen
- **Route:** `/workout/detail/{workout_id}`
- **Analytics:** `screen_workout_detail`
- **Required data:** Workout, WorkoutExercises, WorkoutSets, PersonalRecords
  detected in this workout
- **Actions:** View exercise detail, view PR detail, share (V4)
- **Notes:** Read-only view of a completed workout.

### ExerciseLibraryScreen
- **Route:** `/exercises`
- **Analytics:** `screen_exercise_library`
- **Required data:** Paginated exercise list, filter state
- **Actions:** Search by name, filter by category/muscle group/equipment,
  tap exercise (→ ExerciseDetailScreen), create custom exercise
- **Notes:** Backed by ExerciseDB + user custom exercises.
  Empty search results state: "No exercises found. Try a different search
  or create a custom exercise."

### ExerciseDetailScreen
- **Route:** `/exercises/{id}`
- **Analytics:** `screen_exercise_detail`
- **Required data:** Exercise (name, video URL, muscle groups, instructions),
  user's PR for this exercise (if any), active workout state
- **Actions:** Play exercise video (AVPlayer, if demo_url present),
  contextual workout CTA (see Notes), view PR history (→ PRHistoryScreen)
- **Notes:** Video played via AVPlayer. Custom exercises show no video.
  Primary and secondary muscle groups displayed. Instructions shown below video.
  **Contextual CTA (Decision 89):**
  — Workout in progress: "Add to workout" (→ ActiveWorkoutScreen, exercise appended)
  — No active workout: "Start workout with this exercise" (→ ActiveWorkoutScreen,
    new workout created with this exercise pre-loaded)

### PersonalRecordDetailScreen
- **Route:** `/records/detail/{record_id}`
- **Analytics:** `screen_pr_detail`
- **Required data:** PersonalRecord, previous PersonalRecord, Exercise
- **Actions:** View in workout context (→ WorkoutDetailScreen)
- **Notes:** Shows current record, previous record, improvement delta,
  and date achieved.

### PRHistoryScreen
- **Route:** `/records/history/{exercise_id}`
- **Analytics:** `screen_pr_history`
- **Required data:** All PersonalRecords for this exercise for this user,
  ordered by recorded_at
- **Actions:** Tap record (→ PersonalRecordDetailScreen)
- **Notes:** V2 adds a chart visualisation of PR progression over time.

### FutureSelfScreen
- **Route:** `/future-self`
- **Analytics:** `screen_future_self`
- **Required data:** User's future self image URL, User goal
- **Actions:** Regenerate image (if under monthly limit → PhotoCaptureScreen),
  delete image (with confirmation)
- **Notes:** Shows the generated image with goal context.
  Regeneration limit: 5 per month. Shows remaining count.
  If no image exists and BiometricConsent not given:
  shows prompt to complete Phase 2 onboarding.

### ProfileScreen
- **Route:** `/profile`
- **Analytics:** `screen_profile`
- **Required data:** User profile, workout stats summary
- **Actions:** Edit display name, edit avatar, change units,
  change measurement units, view account settings
- **Notes:** Stats summary: total workouts, total PRs, current streak.

### SettingsScreen
- **Route:** `/settings`
- **Analytics:** `screen_settings`
- **Required data:** User preferences, notification settings, beta_tier
- **Actions:** Manage notifications, manage biometric consent,
  privacy settings, delete account, sign out
- **Notes:** All destructive actions (delete account, revoke consent)
  require confirmation dialogs.

### NotificationSettingsScreen
- **Route:** `/settings/notifications`
- **Analytics:** `screen_notification_settings`
- **Required data:** Current notification preferences
- **Actions:** Enable/disable each notification type,
  set workout reminder time and days,
  set show-up nudge time
- **Notes:** Notification types: PR achieved, workout reminder, show-up nudge.
  Nudge time must be before typical workout time.

### BiometricConsentSettingsScreen
- **Route:** `/settings/biometric-consent`
- **Analytics:** `screen_biometric_consent_settings`
- **Required data:** Current BiometricConsent status
- **Actions:** Revoke consent (deletes photo and generated image,
  disables future self feature), re-consent (→ BiometricConsentScreen)
- **Notes:** Revocation is immediate and irreversible from this screen.
  Deleted data confirmation message shown after revocation.

### DeleteAccountScreen
- **Route:** `/settings/delete-account`
- **Analytics:** `screen_delete_account`
- **Required data:** None
- **Actions:** Confirm deletion (requires typing "DELETE"), cancel
- **Notes:** Account deletion initiates backend deletion job.
  User is signed out immediately.
  Data deleted within 30 days per Privacy Policy.
  This screen cannot be reached without authentication.

---

## Error and System Screens

### OfflineBannerComponent
- **Route:** N/A (persistent banner, shown when offline)
- **Analytics:** `component_offline_banner_shown`
- **Notes:** "You're offline. Changes will sync when you reconnect."
  Non-blocking. App remains fully functional offline.

### ErrorScreen
- **Route:** N/A (shown when navigation fails catastrophically)
- **Analytics:** `screen_error`
- **Required data:** Error type (user-facing message only)
- **Actions:** Retry, go home
- **Notes:** "Something went wrong. We've been notified."
  Never shows stack traces or error codes to users.

---

## V2 Screens (Not Built in V1)

- ProgramBuilderScreen
- ProgramDetailScreen
- BodyMetricsScreen
- StepsAndCaloriesScreen
- ProgressChartsScreen
- BenchmarkingScreen
- SpreadsheetImportScreen

---

## Screen Count Summary

| Phase | Screen count |
|---|---|
| Phase 1 onboarding | 4 |
| Phase 2 onboarding | 5 |
| Main app | 14 |
| Components (inline) | 3 |
| Error/system | 2 |
| **V1 total** | **28** |

