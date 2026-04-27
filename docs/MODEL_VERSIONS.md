# PRLifts — AI Model Version Pinning

**Version:** 1.0
**Last updated:** April 2026
**Owner:** ML Platform Lead
**Audience:** All developers (human and Claude Code)

> AI model versions are pinned explicitly for every feature.
> Never use a "latest" alias in production — model updates can silently
> change behaviour, tone, and output format in ways that break the
> quality gate, prompt evaluation tests, or user experience.

---

## Why Pinning Matters

A model update from Anthropic or Fal.ai can:
- Change the tone or length of insight responses
- Change how the vision model scores face similarity
- Alter the image generation style in ways that fail the quality gate
- Behave differently on edge case inputs your tests don't cover

Pinning means a model change only happens when you decide it happens,
after you have re-run the prompt evaluation suite and confirmed behaviour.

---

## Current Pinned Versions

| Feature | Provider | Model | Pinned version | Pinned since |
|---|---|---|---|---|
| Workout insights | Anthropic | Claude | `claude-sonnet-4-5` | April 2026 |
| Benchmarking | Anthropic | Claude | `claude-sonnet-4-5` | April 2026 |
| Quality gate scoring | Anthropic | Claude (vision) | `claude-sonnet-4-5` | April 2026 |
| Future self generation | Fal.ai | flux/dev | `fal-ai/flux/dev` | April 2026 |

**Why Claude Sonnet 4.5 for all Anthropic calls:**
Sonnet is the appropriate balance of quality and cost for V1 at the usage
volumes expected. Haiku would reduce cost but insight quality is core to
the product's value proposition. Opus is unnecessary cost for these tasks.

---

## Version in Code

All model versions are defined as constants in one place:

```python
# app/config/ai_models.py
# PRLifts AI Model Version Configuration
#
# All AI model versions are pinned here. Never hardcode model
# strings elsewhere in the codebase. When upgrading a model,
# update this file, re-run the prompt evaluation suite, and
# log the upgrade decision in MODEL_VERSIONS.md.

class AIModels:
    # Anthropic Claude — used for insights, benchmarking, quality scoring
    CLAUDE = "claude-sonnet-4-5"

    # Fal.ai — used for future self image generation
    FAL_IMAGE_GENERATION = "fal-ai/flux/dev"
```

```python
# Usage in service code
from app.config.ai_models import AIModels

response = anthropic_client.messages.create(
    model=AIModels.CLAUDE,
    max_tokens=1000,
    messages=[...]
)
```

```swift
// iOS: model versions are not relevant to the client
// The client polls Job status — it does not call AI providers directly
```

---

## Model Upgrade Policy

**Before upgrading any model version:**

1. Update the version constant in `app/config/ai_models.py` in a branch
2. Re-run the full prompt evaluation suite against the new version
3. Compare scores against the baseline (current version)
4. New version must score ≥ current version on all 20 test cases
5. For the future_self quality scoring model: run the blocking test cases
6. Deploy to staging only — verify quality gate behaviour on real images
7. Monitor staging for 48 hours
8. Record the upgrade decision in this document (below)
9. Deploy to production
10. Monitor for 7 days post-upgrade

**Do not upgrade if:**
- Any prompt evaluation test case regresses
- Quality gate failure rate changes by more than ±5%
- Insight response format or length changes materially

---

## Upgrade History

| Date | Feature | Previous version | New version | Reason | Approved by |
|---|---|---|---|---|---|
| April 2026 | All Anthropic | (initial) | `claude-sonnet-4-5` | Initial pinning | ML Platform Lead |
| April 2026 | Image generation | (initial) | `fal-ai/flux/dev` | Initial pinning | ML Platform Lead |

---

## Emergency Rollback

If a model upgrade causes problems in production:

1. Update version constant to previous version in `app/config/ai_models.py`
2. Deploy immediately — this is a one-line change, fast deploy
3. Document in this table what went wrong
4. Open a GitHub issue to investigate before re-attempting the upgrade

Rollback should take under 5 minutes from detection to deployment.

---

## Cost Implications by Model

| Model | Input cost | Output cost | When to use |
|---|---|---|---|
| claude-haiku-4-5 | Lower | Lower | High-volume, short outputs |
| claude-sonnet-4-5 | Medium | Medium | Primary V1 model — quality/cost balance |
| claude-opus-4-5 | Higher | Higher | Complex reasoning tasks (not V1) |

At V1 volumes (< 1,000 users, 60 insights/user/month), Sonnet is appropriate.
Re-evaluate at V2 when actual usage data is available from production.

