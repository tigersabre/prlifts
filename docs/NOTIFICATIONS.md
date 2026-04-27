# PRLifts — Push Notification Payload Catalog

**Version:** 1.0
**Last updated:** April 2026
**Owners:** iOS Platform Lead + Backend Platform Lead
**Audience:** All developers (human and Claude Code)

> Every notification type is defined here: trigger conditions, exact
> APNs payload structure, deep link carried, and rich attachment spec.
> This is the contract between the backend (generates and sends) and
> iOS (displays and handles). Never implement a notification type without
> defining it here first.

---

## Notification Types — V1

Three notification types are active in V1:

| Type | Trigger | Rich attachment | Deep link |
|---|---|---|---|
| `pr_achieved` | WorkoutSet completion with PR detected | None | PersonalRecordDetailScreen |
| `workout_reminder` | User-configured schedule | None | ActiveWorkoutScreen (new) |
| `show_up_nudge` | Scheduled day, no workout by nudge time | Future self image | FutureSelfScreen or HomeScreen |

---

## Permission Strategy

Notification permission is requested in Phase 2 onboarding, after the
future self image is revealed. This is the highest-context moment:
the user has just seen their future self image and understands that
the show-up nudge will include it.

**Never request permission:**
- On first app launch
- Before the user has logged their first workout
- As a cold ask without context

**Permission request copy:**
```
"Stay on track with your goals.
PRLifts can remind you to train on your scheduled days —
complete with your future self image to keep you motivated.

[Allow Notifications]  [Not Now]"
```

---

## Notification Type 1 — PR Achieved (`pr_achieved`)

### Trigger

- Fired immediately when `WorkoutSet.is_completed = true` triggers PR detection
- PR detection confirms new PersonalRecord created
- One notification per PR per workout

### Conditions

- User has notification permission granted
- Workout is not in `paused` status (PR detected on set completion, not workout end)

### APNs Payload

```json
{
  "aps": {
    "alert": {
      "title": "New personal record! 🎉",
      "body": "{exercise_name}: {pr_value} {pr_unit} ({record_type_label})"
    },
    "sound": "pr_achieved.caf",
    "badge": 0,
    "interruption-level": "active"
  },
  "notification_type": "pr_achieved",
  "deep_link": "https://prlifts.app/records/detail/{record_id}",
  "pr_data": {
    "record_id": "{uuid}",
    "exercise_id": "{uuid}",
    "exercise_name": "{string}",
    "pr_value": "{number}",
    "pr_unit": "{kg|lbs|reps|seconds|meters}",
    "previous_value": "{number}",
    "record_type": "{record_type_enum_value}"
  }
}
```

### Record Type Labels (for `body` field)

| record_type | label |
|---|---|
| `heaviest_weight` | "Heaviest lift" |
| `most_reps` | "Most reps" |
| `longest_duration` | "Longest hold" |
| `longest_distance` | "Furthest distance" |
| `best_rpe` | "Easiest performance" |

### Body Examples

- "Bench Press: 225 lbs (Heaviest lift)"
- "Pull-up: 15 reps (Most reps)"
- "Plank: 3 min 20 sec (Longest hold)"

### iOS Handling

```swift
// On tap: navigate to PersonalRecordDetailScreen
// On foreground receipt: show PRNotificationBanner inline on ActiveWorkoutScreen
// No action button required
```

---

## Notification Type 2 — Workout Reminder (`workout_reminder`)

### Trigger

- User-configured schedule: specific days of week at a specific time
- Fired by the backend APScheduler at the configured time
- Only fired on configured days

### User Configuration

On NotificationSettingsScreen, user sets:
- Days of week (multi-select: Mon, Tue, Wed, Thu, Fri, Sat, Sun)
- Time of day (time picker)

Stored on User record in Supabase:
```json
{
  "workout_reminder_days": [1, 3, 5],
  "workout_reminder_time": "07:00",
  "workout_reminder_timezone": "America/Los_Angeles"
}
```

### APNs Payload

```json
{
  "aps": {
    "alert": {
      "title": "Time to train",
      "body": "Your workout is scheduled for today. Ready when you are."
    },
    "sound": "default",
    "badge": 0,
    "interruption-level": "time-sensitive"
  },
  "notification_type": "workout_reminder",
  "deep_link": "https://prlifts.app/workout/start"
}
```

### iOS Handling

```swift
// On tap: navigate to ActiveWorkoutScreen to start a new workout
// On foreground receipt: show non-intrusive banner only
```

---

## Notification Type 3 — Show-up Nudge (`show_up_nudge`)

### Purpose

A single motivational nudge on a scheduled workout day when no workout
has been logged. Uses tiny habits framing — the ask is as small as possible.
Includes the future self image as a rich attachment when available.

### Trigger Conditions (ALL must be true)

1. Today is a day configured in user's workout reminder schedule
2. Current time has passed the user's configured nudge time
3. No workout with `status IN (in_progress, paused, completed, partial_completion)`
   has been started today (any workout logged today, regardless of completion)
4. The nudge has not already been sent today
5. User has notification permission granted

### Nudge Time Configuration

User sets nudge time separately from reminder time:
- Nudge time defaults to 2 hours after reminder time
- Nudge time must be after reminder time
- Minimum: reminder time + 1 hour
- Maximum: 10 PM in user's timezone

### Copy — Tiny Habits Framing

Copy varies based on whether the user has a future self image:

**With future self image:**
```
Title: "This is where you're headed"
Body: "Just show up. One set is all it takes."
```

**Without future self image:**
```
Title: "Today's a workout day"
Body: "You don't have to crush it — just show up and do one thing."
```

**Copy rules:**
- Never use: "Don't break your streak", "You haven't worked out", "You missed"
- Always frame positively — toward the goal, not away from failure
- Maximum one nudge per day — never a follow-up nudge

### APNs Payload — With Future Self Image

```json
{
  "aps": {
    "alert": {
      "title": "This is where you're headed",
      "body": "Just show up. One set is all it takes."
    },
    "sound": "default",
    "badge": 0,
    "interruption-level": "passive",
    "mutable-content": 1
  },
  "notification_type": "show_up_nudge",
  "deep_link": "https://prlifts.app/future-self",
  "future_self_image_url": "{signed_supabase_storage_url}"
}
```

`mutable-content: 1` enables the iOS Notification Service Extension to
download the image before display.

### APNs Payload — Without Future Self Image

```json
{
  "aps": {
    "alert": {
      "title": "Today's a workout day",
      "body": "You don't have to crush it — just show up and do one thing."
    },
    "sound": "default",
    "badge": 0,
    "interruption-level": "passive"
  },
  "notification_type": "show_up_nudge",
  "deep_link": "https://prlifts.app/home"
}
```

### iOS Notification Service Extension

Required for rich attachment (image download before display):

```swift
// NotificationService.swift
// PRLifts iOS App
//
// Notification Service Extension — downloads the future self image
// before the show_up_nudge notification is displayed.
// Only runs when mutable-content = 1 in the APNs payload.

class NotificationService: UNNotificationServiceExtension {

    override func didReceive(
        _ request: UNNotificationRequest,
        withContentHandler contentHandler: @escaping (UNNotificationContent) -> Void
    ) {
        let content = request.content.mutableCopy() as! UNMutableNotificationContent

        guard
            let imageURLString = request.content.userInfo["future_self_image_url"] as? String,
            let imageURL = URL(string: imageURLString)
        else {
            contentHandler(content)
            return
        }

        // Download image — extension has 30 seconds before iOS kills it
        URLSession.shared.dataTask(with: imageURL) { data, _, error in
            defer { contentHandler(content) }
            guard let data, error == nil else { return }

            let tempDir = FileManager.default.temporaryDirectory
            let imageFile = tempDir.appendingPathComponent("future_self.jpg")

            guard (try? data.write(to: imageFile)) != nil,
                  let attachment = try? UNNotificationAttachment(
                      identifier: "future_self",
                      url: imageFile,
                      options: nil
                  )
            else { return }

            content.attachments = [attachment]
        }.resume()
    }
}
```

### iOS Handling

```swift
// On tap: navigate to FutureSelfScreen (with image) or HomeScreen (without)
// On foreground receipt: suppress — do not show banner if user is actively using app
```

---

## Backend — APScheduler Jobs for Notifications

```python
# Scheduled jobs for notification delivery
# All run via APScheduler AsyncIOScheduler in the FastAPI lifespan

scheduler.add_job(
    send_workout_reminders,
    "cron",
    minute=0,          # Check at the top of every hour
    id="workout_reminders"
)

scheduler.add_job(
    send_show_up_nudges,
    "cron",
    minute=30,         # Check at :30 past every hour
    id="show_up_nudges"
)
```

### `send_workout_reminders` Logic

```python
async def send_workout_reminders():
    """
    Sends workout reminder notifications to users whose configured
    reminder time falls within the last hour and who have not already
    received a reminder today.

    Runs hourly. Only sends within a 60-minute window of the configured time
    to avoid sending late reminders.
    """
    now_utc = datetime.utcnow()
    # Query users where today is a configured reminder day
    # and reminder_time (in their timezone) is within the last 60 minutes
    # and no reminder has been sent today
    ...
```

---

## Notification Delivery Failures

APNs delivery is best-effort. The backend does not retry failed notifications.

If APNs returns:
- `400 Bad Request` → log as WARNING (invalid token format or payload)
- `403 Forbidden` → log as ERROR (invalid certificate — requires investigation)
- `410 Gone` → delete the device token (device no longer registered)
- `429 Too Many Requests` → log as WARNING, no retry in V1

Device token management:
- Tokens registered on app launch if permission granted
- Tokens deleted from backend when APNs returns 410
- New token sent on each app launch (tokens can rotate)

