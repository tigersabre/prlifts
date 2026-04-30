"""
ai_models.py
PRLifts Backend

Pinned AI model version constants. All model identifiers are defined here —
never hardcode model strings elsewhere. When upgrading a model, update this
file, re-run the prompt evaluation suite, and log the decision in
docs/MODEL_VERSIONS.md.

See docs/MODEL_VERSIONS.md for upgrade history and policy.
"""


class AIModels:
    CLAUDE = "claude-sonnet-4-5"
    FAL_IMAGE_GENERATION = "fal-ai/flux/dev"
