# PRLifts — Seed Data Reference

**Version:** 1.0
**Last updated:** April 2026
**Owner:** Data Architect
**Audience:** All developers (human and Claude Code)

> Seed data is the initial data the database needs before the app is usable.
> Without it, the exercise library is empty and the AI has no prompt templates.
> Every environment (development, staging, production) requires seed data.
> Seed scripts live in `backend/seeds/` and are run after migrations.

---

## Why Seed Data Matters

If seed data is missing:
- The exercise library returns empty results on first launch
- ExerciseDB import has not run — users cannot find exercises
- PromptTemplate table has no active prompts — AI jobs fail immediately
- Tests fail because they depend on known exercise IDs

---

## Seed Script Execution Order

```
1. run_migrations.py        ← schema must exist first
2. seed_exercises.py        ← populate exercise library from ExerciseDB
3. seed_prompt_templates.py ← create initial AI prompts
4. seed_test_data.py        ← development and staging only (NOT production)
```

---

## 1. Exercise Library Seed (`seed_exercises.py`)

**Source:** ExerciseDB API via RapidAPI
**Target table:** `exercise`
**Environment:** All environments

### What It Does

Fetches all exercises from ExerciseDB and inserts them with
`is_custom = false` and `created_by = null`. Maps ExerciseDB fields
to the PRLifts schema.

### ExerciseDB → PRLifts Field Mapping

| ExerciseDB field | PRLifts field | Notes |
|---|---|---|
| `id` | Not stored | ExerciseDB ID not needed — we use our own UUID |
| `name` | `name` | Titlecased |
| `bodyPart` | `muscle_group` | Mapped via lookup table below |
| `target` | `muscle_group` | Used when bodyPart is too broad |
| `secondaryMuscles` | `secondary_muscle_groups` | Array mapped to muscle_group enum |
| `equipment` | `equipment` | Mapped via lookup table below |
| `gifUrl` | `demo_url` | Direct URL |
| `instructions` | `instructions` | Joined array of instruction strings |

### ExerciseDB → muscle_group Mapping

```python
BODY_PART_MAP = {
    "chest": "mid_chest",       # Default — refine with target field
    "back": "upper_back",       # Default
    "shoulders": "shoulders",
    "upper arms": "biceps",     # Refined by target
    "lower arms": "biceps",     # Refined by target
    "upper legs": "quads",      # Refined by target
    "lower legs": "calves",     # Refined by target
    "waist": "abs",
    "cardio": "full_body",
    "neck": "full_body",
}

TARGET_OVERRIDES = {
    "pectorals": "mid_chest",
    "upper chest": "upper_chest",
    "lower chest": "lower_chest",
    "lats": "upper_back",
    "traps": "upper_back",
    "lower back": "lower_back",
    "spine": "lower_back",
    "triceps": "triceps",
    "biceps": "biceps",
    "forearms": "biceps",
    "quads": "quads",
    "hamstrings": "hamstrings",
    "glutes": "glutes",
    "calves": "calves",
    "abductors": "glutes",
    "adductors": "quads",
    "abs": "abs",
    "obliques": "obliques",
    "cardiovascular system": "full_body",
}
```

### ExerciseDB → equipment Mapping

```python
EQUIPMENT_MAP = {
    "barbell": "barbell",
    "dumbbell": "dumbbell",
    "kettlebell": "kettlebell",
    "cable": "cable",
    "machine": "machine",
    "leverage machine": "machine",
    "smith machine": "machine",
    "body weight": "bodyweight",
    "assisted": "bodyweight",   # Assisted exercises are bodyweight category
    "band": "other",
    "roller": "other",
    "rope": "other",
    "stability ball": "other",
    "tire": "other",
    "trap bar": "barbell",      # Treat as barbell variant
    "weighted": "other",
    "ez barbell": "barbell",    # Treat as barbell variant
    "olympic barbell": "barbell",
    "hammer": "other",
    "sled machine": "machine",
    "stationary bike": "cardio_machine",
    "skierg machine": "cardio_machine",
    "upper body ergometer": "cardio_machine",
}
```

### Expected Exercise Count

ExerciseDB contains approximately 1,300+ exercises. After mapping,
expect 1,200–1,300 exercises in the database. Some exercises may be
skipped if their category or equipment cannot be mapped.

All skipped exercises are logged to `seeds/logs/exercise_seed_errors.log`.

---

## 2. Prompt Template Seed (`seed_prompt_templates.py`)

**Target table:** `prompt_template`
**Environment:** All environments

### Initial Prompt Templates

Three templates must exist before any AI feature can run:

#### insight v1.0

```python
{
    "feature": "insight",
    "version": "v1.0",
    "is_active": True,
    "prompt_text": """[ROLE]
You are a fitness coach AI for PRLifts, a workout tracking app.
Your role is to provide a brief, encouraging post-workout insight.

[CONTEXT]
User goal: {goal}
Workout format: {format}
Workout date: {date}
Exercises performed:
{exercises_summary}
Personal records achieved: {pr_summary}
Previous workout (if any): {previous_workout_summary}

[TASK]
Write a single, specific insight about this workout. Focus on:
- A PR achieved (if any) — celebrate it
- A noticeable pattern or improvement vs previous workout
- An encouraging observation about volume, consistency, or effort

[CONSTRAINTS]
- Maximum 2 sentences
- Specific to the data above — no generic fitness advice
- Never give medical advice
- Frame as encouragement, not criticism
- If data is insufficient for a meaningful insight, say so briefly
- Never use the phrases: lose weight, burn fat, slim down, thinner

[OUTPUT FORMAT]
Plain text only. No markdown. No bullet points. 2 sentences maximum."""
}
```

#### future_self v1.0

```python
{
    "feature": "future_self",
    "version": "v1.0",
    "is_active": True,
    "prompt_text": """[ROLE]
You are scoring an AI-generated fitness transformation image
for quality and accuracy.

[TASK]
Score the similarity between the original photo and the generated image
on a scale of 1 to 10, where:
1 = completely different person, no resemblance
5 = some facial similarity, clearly same general appearance
10 = highly convincing, clearly the same person

Focus on: facial structure, skin tone, hair colour and style,
distinctive features.

[CONSTRAINTS]
- Score the face and identity similarity only
- Ignore clothing, body size/shape differences (expected to differ)
- Ignore background
- Return only the numeric score, nothing else

[OUTPUT FORMAT]
A single integer between 1 and 10. Nothing else."""
}
```

Note: The actual image generation prompt used to call Fal.ai is
constructed in code (not in PromptTemplate) because it includes
the structured image-to-image instruction format specific to
the Fal.ai API. The prompt_template for feature: future_self
is used exclusively for the Claude vision quality scoring call.

#### benchmarking v1.0

```python
{
    "feature": "benchmarking",
    "version": "v1.0",
    "is_active": True,
    "prompt_text": """[ROLE]
You are a fitness data analyst for PRLifts.

[CONTEXT]
User profile:
- Age: {age} (or 'not provided')
- Gender: {gender} (or 'not provided')
- Goal: {goal} (or 'not provided')

Exercise: {exercise_name}
User's personal record: {pr_value} {pr_unit}
Record type: {record_type}

[TASK]
Provide a brief, accurate benchmark comparison for this personal record.
Use established strength standards (e.g. ExRx, Symmetric Strength) appropriate
for the user's age and gender if provided.

[CONSTRAINTS]
- Maximum 2 sentences
- If age/gender not provided, note that comparison is approximate
- Use encouraging but accurate framing
- Never claim the user is in a specific percentile without data to support it
- Frame as "relative to general population" not "compared to other users"
- Never give medical advice

[OUTPUT FORMAT]
Plain text only. 2 sentences maximum."""
}
```

---

## 3. Test Data Seed (`seed_test_data.py`)

**Environment:** Development and staging ONLY — never production
**Purpose:** Creates realistic test data so features can be developed
and tested without manual data entry

### Test User Accounts

```python
TEST_USERS = [
    {
        "email": "test.beginner@prlifts.test",
        "display_name": "Alex Beginner",
        "unit_preference": "lbs",
        "goal": "build_muscle",
        "gender": "na",
        # Has 5 workouts over 2 weeks, no PRs
    },
    {
        "email": "test.intermediate@prlifts.test",
        "display_name": "Sam Intermediate",
        "unit_preference": "kg",
        "goal": "improve_endurance",
        "gender": "female",
        # Has 30 workouts over 3 months, several PRs, active future self
    },
    {
        "email": "test.advanced@prlifts.test",
        "display_name": "Jordan Advanced",
        "unit_preference": "lbs",
        "goal": "athletic_performance",
        "gender": "male",
        # Has 100+ workouts, many PRs, full feature usage
    },
    {
        "email": "test.empty@prlifts.test",
        "display_name": "Casey Empty",
        "unit_preference": "lbs",
        "goal": None,
        # New user — Phase 1 complete, no workouts logged
    },
]
```

### Known Exercise IDs for Testing

These exercises are guaranteed to exist after seeding and can be
referenced by ID in test code:

```python
# Use these names to look up IDs after seeding
KNOWN_EXERCISES = {
    "bench_press_barbell": "Bench Press",          # strength, mid_chest, barbell
    "squat_barbell": "Barbell Squat",               # strength, quads, barbell
    "deadlift_barbell": "Deadlift",                 # strength, lower_back, barbell
    "pull_up_bodyweight": "Pull-up",                # strength, upper_back, bodyweight
    "running_treadmill": "Running",                  # cardio, full_body, cardio_machine
    "plank_bodyweight": "Plank",                    # strength, abs, bodyweight
    "bicep_curl_dumbbell": "Dumbbell Bicep Curl",   # strength, biceps, dumbbell
}
```

Do not hardcode UUIDs in test code — look up by name after seeding:

```python
# In test setup
bench_press = db.query(Exercise).filter_by(name="Bench Press").first()
BENCH_PRESS_ID = bench_press.id
```

---

## Running Seeds

### Development

```bash
cd backend
python seeds/run_migrations.py
python seeds/seed_exercises.py          # takes 2-5 minutes (API calls)
python seeds/seed_prompt_templates.py
python seeds/seed_test_data.py          # development only
```

### Staging

```bash
# Run as part of Railway deployment pipeline
python seeds/run_migrations.py
python seeds/seed_exercises.py
python seeds/seed_prompt_templates.py
python seeds/seed_test_data.py          # staging only
```

### Production

```bash
# Run manually after first deployment and after each migration
python seeds/run_migrations.py
python seeds/seed_exercises.py
python seeds/seed_prompt_templates.py
# DO NOT run seed_test_data.py on production
```

### Re-seeding Exercises

The exercise seed script is idempotent — safe to re-run. It uses
`INSERT ... ON CONFLICT (name) DO UPDATE` so existing exercises
are updated with fresh ExerciseDB data without creating duplicates.

Re-seed exercises when:
- ExerciseDB adds significant new exercises (quarterly check recommended)
- A mapping error is discovered and corrected

