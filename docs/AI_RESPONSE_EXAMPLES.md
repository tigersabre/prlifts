# PRLifts — AI Response Examples Library

**Version:** 1.0
**Last updated:** April 2026
**Owner:** ML Platform Lead
**Audience:** All developers (human and Claude Code)

> This library shows what "good" and "bad" AI responses look like.
> It is used for:
> 1. Onboarding new developers to expected AI quality
> 2. Calibrating the prompt evaluation test cases
> 3. Prompt iteration reference — what are we aiming for?
> 4. Debugging quality gate behaviour

---

## Feature: Workout Insight

### Good Responses

**Good — PR achieved, specific and encouraging:**
> "New bench press record at 225 lbs — that's a solid 10-lb jump from last week. Your upper body strength is building consistently."

Why this is good:
- Names the exercise and the specific weight
- Quantifies the improvement (10-lb jump)
- Forward-looking framing (building consistently)
- Under 2 sentences, under 280 characters

---

**Good — No PR, volume observation:**
> "You added a full extra set to your squat work today compared to last Thursday — the volume increase is exactly the kind of progressive overload that builds strength over time."

Why this is good:
- Specific observation (extra set vs last Thursday)
- Explains the mechanism (progressive overload)
- Educational without being condescending

---

**Good — First workout:**
> "Every strong lifter started exactly where you are today. Showing up and completing your first workout is the hardest part — it gets easier from here."

Why this is good:
- Appropriate for a first workout (no comparison to make)
- Motivational without being hollow
- Does not fabricate observations about data that doesn't exist

---

**Good — Cardio workout:**
> "5.2 km is a new distance PR — you went a little further than last time and still ran it in about the same time. Your endurance base is growing."

Why this is good:
- Uses distance, not weight (contextually appropriate for cardio)
- Specific to the data provided
- No strength-lifting language in a cardio context

---

**Good — RPE-based insight:**
> "225 lbs at RPE 6 is meaningfully different from the same weight at RPE 8 a few weeks ago — you're getting stronger even when the numbers look the same."

Why this is good:
- Explains what RPE means in plain English
- Makes a non-obvious insight accessible to a non-technical user
- Specific to the user's actual data

---

### Bad Responses — With Explanations

**Bad — Generic and hollow:**
> "Great workout! Keep up the good work and you'll reach your goals!"

Why this is bad:
- References no specific data from the workout
- Could have been written without reading anything
- Provides zero value

---

**Bad — Forbidden phrase (weight loss language):**
> "A great cardio workout — you're on your way to burning fat and losing weight efficiently."

Why this is bad:
- "burning fat" and "losing weight" are forbidden phrases
- Framing around weight loss, not performance

---

**Bad — Forbidden phrase (medical language):**
> "You noted knee discomfort — you may be experiencing early signs of patellofemoral syndrome. Consider seeing a physiotherapist."

Why this is bad:
- Medical diagnostic language
- Diagnosing a condition ("patellofemoral syndrome")
- Recommending medical action

---

**Bad — Too long:**
> "Today was a really great workout overall. You hit a new personal record on the bench press with 225 lbs, which is impressive. Your form has clearly been improving, and the progressive overload approach you've been taking is paying off in a big way. I can see from your history that you've been consistent over the past few weeks, and that consistency is what separates people who make progress from those who don't. Keep showing up like this and you'll continue to see results. Remember, recovery is just as important as training, so make sure you're getting enough sleep and nutrition to support your hard work."

Why this is bad:
- Way over 2 sentences and 280 characters
- Makes claims about "form" that no data supports
- Generic advice not grounded in specific workout data
- Preachy and unsolicited advice about recovery/sleep

---

**Bad — Fabricated data:**
> "Your squat is in the top 25% for your age and weight category, which is excellent."

Why this is bad:
- We do not have benchmarking data for this user in a workout insight context
- This is a fabricated statistic
- Benchmarking is a separate feature with its own prompt

---

## Feature: Quality Gate Scoring

### Good Scoring Responses

These are the exact responses the quality gate prompt should produce.
They are single integers, nothing else.

**High similarity:** `8`
**Medium similarity:** `5`
**Low similarity:** `2`

### Bad Scoring Responses

**Bad — Includes explanation:**
> "I would rate this a 7 out of 10. The facial structure is similar and the skin tone matches, but the hair colour is slightly different in the generated image."

Why this is bad:
- Prompt says "A single integer between 1 and 10. Nothing else."
- The explanation cannot be parsed as an integer
- This would cause the quality gate to fail and trigger the fail-closed path

**Bad — Out of range:**
> "10/10"

Why this is bad:
- `10/10` is not parseable as a simple integer
- The prompt should produce `10` not `10/10`

---

## Feature: Benchmarking

### Good Responses

**Good — Known demographics, known exercise:**
> "A 225 lb bench press is considered intermediate-to-advanced strength for a 30-year-old male — most people with a few years of consistent training land in this range. It's a meaningful milestone worth building on."

Why this is good:
- Honest, approximate comparison
- Does not claim a false precision ("67th percentile")
- Uses general population framing
- Specific to the exercise and demographic

---

**Good — No demographics:**
> "Without knowing your age or gender, a rough comparison is hard to give — but 225 lbs on bench is a weight that takes most people months or years of consistent work to reach. That's not a trivial number."

Why this is good:
- Honest about limitation
- Still provides useful context
- Does not pretend to have data it does not have

---

**Good — Niche exercise:**
> "Turkish Get-Ups at 70 lbs are genuinely difficult — there's limited population data for this movement, but that weight is well into advanced territory for most practitioners of the lift."

Why this is good:
- Honest about limited data for niche exercises
- Does not fabricate a percentile
- Still provides meaningful context

---

### Bad Responses

**Bad — False precision:**
> "You are in the 73rd percentile for bench press strength among males aged 28-32."

Why this is bad:
- We do not have access to a database that supports this claim
- Fabricated statistics erode trust
- Forbidden by the benchmarking prompt constraints

**Bad — Absolute claim:**
> "You will definitely be able to hit 250 lbs within the next 3 months if you maintain this rate of progress."

Why this is bad:
- "You will" is a forbidden absolute claim
- Predicting future performance is outside the scope and knowledge of the system

