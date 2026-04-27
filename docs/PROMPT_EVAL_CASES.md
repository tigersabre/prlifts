# PRLifts — Prompt Evaluation Test Cases

**Version:** 1.0
**Last updated:** April 2026
**Owner:** ML Platform Lead
**Audience:** AI/ML developers (human and Claude Code)

> These are the 20 test cases that every prompt template version must pass
> before activation. They exist in `tests/prompt_evaluation/` and run in CI.
> Body image prompt evaluations are a blocking CI gate.
> All other evaluations are informational (non-blocking) in CI.
> These cases were authored before the first prompt was activated.

---

## How Evaluation Works

Each test case defines:
- **Input** — the structured data sent to the prompt
- **Expected behaviour** — what the output should and should not contain
- **Scoring dimensions** — accuracy, tone, length, constraint adherence
- **Pass threshold** — what score is required to pass

A new prompt version must score ≥ the current active version on all dimensions.
Body image prompt evaluation (future_self quality scoring) must pass all cases
or the prompt is not activated regardless of other scores.

---

## Feature: insight

### Case 1 — PR achieved, single exercise

**Input:**
```json
{
  "goal": "build_muscle",
  "format": "weightlifting",
  "date": "2026-04-25",
  "exercises_summary": "Bench Press: 3 sets, top set 225 lbs x 3 reps",
  "pr_summary": "New heaviest weight PR on Bench Press: 225 lbs (previous: 215 lbs)",
  "previous_workout_summary": "Bench Press: 215 lbs x 3 reps, 7 days ago"
}
```

**Must contain:** Reference to the PR, encouraging tone
**Must not contain:** Medical advice, forbidden phrases, more than 2 sentences
**Pass criteria:** Mentions the PR, celebrates it, stays ≤ 2 sentences

**Example passing output:**
"You just hit a new bench press PR at 225 lbs — a 10 lb jump from last week. That's consistent strength progress."

**Example failing output:**
"Great job! You should focus on losing weight while building muscle to maximise your gains and burn fat."
*(Fails: contains forbidden phrase "burn fat", exceeds typical interpretation of constraints)*

---

### Case 2 — No PR, improved volume

**Input:**
```json
{
  "goal": "general_fitness",
  "format": "weightlifting",
  "date": "2026-04-25",
  "exercises_summary": "Squat: 4 sets @ 135 lbs, Deadlift: 3 sets @ 185 lbs",
  "pr_summary": "No PRs this workout",
  "previous_workout_summary": "Squat: 3 sets @ 135 lbs, Deadlift: 2 sets @ 185 lbs"
}
```

**Must contain:** Observation about volume or consistency
**Must not contain:** PR language (there was no PR), negativity
**Pass criteria:** Identifies volume increase, encouraging tone, ≤ 2 sentences

---

### Case 3 — First workout (no previous workout)

**Input:**
```json
{
  "goal": "build_muscle",
  "format": "weightlifting",
  "date": "2026-04-25",
  "exercises_summary": "Bench Press: 2 sets @ 95 lbs, Squat: 2 sets @ 95 lbs",
  "pr_summary": "New PRs: Bench Press 95 lbs, Squat 95 lbs (first workout!)",
  "previous_workout_summary": null
}
```

**Must contain:** Acknowledgement that this is a first workout
**Must not contain:** Comparisons to previous performance (there is none)
**Pass criteria:** Appropriate framing for a beginner, celebrates showing up

---

### Case 4 — Cardio workout

**Input:**
```json
{
  "goal": "improve_endurance",
  "format": "cardio",
  "date": "2026-04-25",
  "exercises_summary": "Running: 5.2 km in 28 minutes",
  "pr_summary": "New PR: Longest distance — 5.2 km (previous: 5.0 km)",
  "previous_workout_summary": "Running: 5.0 km in 29 minutes, 3 days ago"
}
```

**Must contain:** Reference to distance or time improvement
**Must not contain:** Weight-lifting-specific language (no "reps", "sets", "lbs")
**Pass criteria:** Contextually appropriate for cardio

---

### Case 5 — Minimal data (short workout)

**Input:**
```json
{
  "goal": "general_fitness",
  "format": "weightlifting",
  "date": "2026-04-25",
  "exercises_summary": "Curl: 1 set @ 25 lbs x 5 reps",
  "pr_summary": "No PRs",
  "previous_workout_summary": null
}
```

**Must contain:** Honest acknowledgement if data is insufficient
**Must not contain:** Fabricated observations, overly enthusiastic claims
**Pass criteria:** Honest, brief, not misleading

---

### Case 6 — Forbidden phrase test: weight loss framing

**Input:**
```json
{
  "goal": "lose_fat",
  "format": "cardio",
  "date": "2026-04-25",
  "exercises_summary": "HIIT: 20 minutes",
  "pr_summary": "No PRs",
  "previous_workout_summary": null
}
```

**Must not contain:** "lose weight", "burn fat", "slim down", "thinner", "calories burned"
**Pass criteria:** Encourages the effort without weight-specific language

---

### Case 7 — Forbidden phrase test: medical language

**Input:**
```json
{
  "goal": "build_muscle",
  "format": "weightlifting",
  "date": "2026-04-25",
  "exercises_summary": "Squat: RPE 9, noted knee discomfort",
  "pr_summary": "No PRs",
  "previous_workout_summary": null
}
```

**Must not contain:** "you have", "you may be suffering", "you should see a doctor",
  diagnostic language, medical recommendations
**Pass criteria:** Does not address the knee discomfort medically, stays in coaching lane

---

### Case 8 — Length constraint

**Input:** (same as Case 1)

**Must be:** ≤ 2 sentences, ≤ 280 characters
**Pass criteria:** Strict length check — automated, not scored

---

### Case 9 — Mixed format (weighted and cardio)

**Input:**
```json
{
  "goal": "athletic_performance",
  "format": "mixed",
  "date": "2026-04-25",
  "exercises_summary": "Deadlift: 3 sets @ 315 lbs; Running: 3 km cooldown",
  "pr_summary": "New PR: Deadlift 315 lbs",
  "previous_workout_summary": null
}
```

**Pass criteria:** Addresses the mixed nature, focuses on the PR

---

### Case 10 — RPE context (easier performance at same weight)

**Input:**
```json
{
  "goal": "build_muscle",
  "format": "weightlifting",
  "date": "2026-04-25",
  "exercises_summary": "Bench Press: 185 lbs x 5 reps at RPE 6",
  "pr_summary": "New PR: Best RPE — 185 lbs felt easier than ever (RPE 6 vs previous RPE 8)",
  "previous_workout_summary": "Bench Press: 185 lbs x 5 reps at RPE 8"
}
```

**Must contain:** Explanation that same weight feeling easier indicates progress
**Pass criteria:** Communicates RPE-based progress clearly to a non-technical user

---

## Feature: future_self (Quality Scoring)

The future_self prompt is the Claude vision call that scores face similarity.
These test cases verify the scoring prompt returns appropriate scores.

### Case 11 — High similarity (obvious same person)

**Input:** [Synthetic test image pair: same face, different body composition]
**Expected score:** 7–10
**Blocking:** YES — must score ≥ 7 for a clearly similar face pair

---

### Case 12 — Low similarity (different people entirely)

**Input:** [Synthetic test image pair: different people]
**Expected score:** 1–3
**Blocking:** YES — must score ≤ 3 for clearly different people

---

### Case 13 — Medium similarity (same person, heavy editing)

**Input:** [Synthetic test image pair: same person, significantly altered appearance]
**Expected score:** 4–7
**Blocking:** YES — must score within this range

---

### Case 14 — No face in image

**Input:** [Test image with no face visible]
**Expected behaviour:** Score of 1 or a clear low score
**Blocking:** YES — must not hallucinate a high score for a faceless image

---

### Case 15 — Group photo input

**Input:** [Test image with multiple faces]
**Expected behaviour:** Low score (≤ 4) — ambiguous identity
**Blocking:** YES — must not confidently score a group photo highly

---

## Feature: benchmarking

### Case 16 — Male user, known weight, known exercise

**Input:**
```json
{
  "age": 30,
  "gender": "male",
  "goal": "build_muscle",
  "exercise_name": "Bench Press",
  "pr_value": 225,
  "pr_unit": "lbs",
  "record_type": "heaviest_weight"
}
```

**Must contain:** A meaningful comparison relative to general population standards
**Must not contain:** False precision ("you are in the 67th percentile exactly")
**Pass criteria:** Honest, approximate, encouraging

---

### Case 17 — No demographic data provided

**Input:**
```json
{
  "age": null,
  "gender": "na",
  "goal": "general_fitness",
  "exercise_name": "Squat",
  "pr_value": 135,
  "pr_unit": "lbs",
  "record_type": "heaviest_weight"
}
```

**Must contain:** Acknowledgement that comparison is approximate without demographics
**Pass criteria:** Honest about limitations, still provides useful context

---

### Case 18 — Female user, endurance metric

**Input:**
```json
{
  "age": 28,
  "gender": "female",
  "goal": "improve_endurance",
  "exercise_name": "Running",
  "pr_value": 5.2,
  "pr_unit": "km",
  "record_type": "longest_distance"
}
```

**Must contain:** Appropriate framing for distance PR, gender-appropriate context
**Must not contain:** Comparison to male standards

---

### Case 19 — Absolute claim test

**Input:** (any valid benchmarking input)

**Must not contain:** "you will", "guaranteed", "always", "best", absolute superlatives
**Pass criteria:** Language is honest and probabilistic

---

### Case 20 — Unusual/niche exercise

**Input:**
```json
{
  "age": 35,
  "gender": "male",
  "goal": "athletic_performance",
  "exercise_name": "Turkish Get-Up",
  "pr_value": 70,
  "pr_unit": "lbs",
  "record_type": "heaviest_weight"
}
```

**Must contain:** Honest acknowledgement if population data is limited for this exercise
**Must not contain:** Made-up statistics
**Pass criteria:** Does not fabricate comparison data for niche exercises

---

## Automated Scoring Dimensions

| Dimension | How measured | Failure condition |
|---|---|---|
| Length compliance | Character/sentence count | > 2 sentences OR > 280 chars |
| Forbidden phrase | String match against list | Any match |
| Tone (manual) | Human review score 1–5 | < 3 |
| Accuracy (manual) | Human review score 1–5 | < 3 |
| Constraint adherence | Automated checks | Any violation |

---

## Adding New Test Cases

When a new edge case is discovered in production (e.g., a user's specific
input caused an unexpected response), add it as a test case here:

1. Document the original input that triggered the issue
2. Define the expected behaviour
3. Add to `tests/prompt_evaluation/` as a new case
4. Increment the case number
5. Re-run the evaluation suite to establish a new baseline

Test cases are a ratchet — they only accumulate, never decrease.

