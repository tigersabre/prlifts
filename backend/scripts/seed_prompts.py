#!/usr/bin/env python3
"""
seed_prompts.py
PRLifts Backend — Scripts

Seeds the three initial PromptTemplate records required for AI features to
function: insight v1.0, future_self v1.0, and benchmarking v1.0. Idempotent
— uses INSERT ... ON CONFLICT targeting the partial unique index on
(feature) WHERE is_active = TRUE, so re-running updates the prompt text
of the existing active template without creating duplicates.

Usage (from backend/):
    python scripts/seed_prompts.py

Environment variables required (read from environment or .env.local):
    DATABASE_URL    asyncpg connection string (postgresql+asyncpg://...)

See docs/SEED_DATA.md § 2 for the authoritative prompt template content.
"""

import asyncio
import logging
import os
import sys
from typing import Any

import asyncpg
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Template definitions — copied verbatim from docs/SEED_DATA.md § 2.
# These are the canonical V1.0 prompts. To iterate on a prompt, create a new
# version via seed_prompts.py with an updated version string, or update this
# list and re-run — the ON CONFLICT clause updates the active record in-place.
# ---------------------------------------------------------------------------

PROMPT_TEMPLATES: list[dict[str, Any]] = [
    {
        "feature": "insight",
        "version": "v1.0",
        "is_active": True,
        "prompt_text": (
            "[ROLE]\n"
            "You are a fitness coach AI for PRLifts, a workout tracking app.\n"
            "Your role is to provide a brief, encouraging post-workout insight.\n"
            "\n"
            "[CONTEXT]\n"
            "User goal: {goal}\n"
            "Workout format: {format}\n"
            "Workout date: {date}\n"
            "Exercises performed:\n"
            "{exercises_summary}\n"
            "Personal records achieved: {pr_summary}\n"
            "Previous workout (if any): {previous_workout_summary}\n"
            "\n"
            "[TASK]\n"
            "Write a single, specific insight about this workout. Focus on:\n"
            "- A PR achieved (if any) — celebrate it\n"
            "- A noticeable pattern or improvement vs previous workout\n"
            "- An encouraging observation about volume, consistency, or effort\n"
            "\n"
            "[CONSTRAINTS]\n"
            "- Maximum 2 sentences\n"
            "- Specific to the data above — no generic fitness advice\n"
            "- Never give medical advice\n"
            "- Frame as encouragement, not criticism\n"
            "- If data is insufficient for a meaningful insight, say so briefly\n"
            "- Never use the phrases: lose weight, burn fat, slim down, thinner\n"
            "\n"
            "[OUTPUT FORMAT]\n"
            "Plain text only. No markdown. No bullet points. 2 sentences maximum."
        ),
    },
    {
        "feature": "future_self",
        "version": "v1.0",
        "is_active": True,
        "prompt_text": (
            "[ROLE]\n"
            "You are scoring an AI-generated fitness transformation image\n"
            "for quality and accuracy.\n"
            "\n"
            "[TASK]\n"
            "Score the similarity between the original photo and the generated image\n"
            "on a scale of 1 to 10, where:\n"
            "1 = completely different person, no resemblance\n"
            "5 = some facial similarity, clearly same general appearance\n"
            "10 = highly convincing, clearly the same person\n"
            "\n"
            "Focus on: facial structure, skin tone, hair colour and style,\n"
            "distinctive features.\n"
            "\n"
            "[CONSTRAINTS]\n"
            "- Score the face and identity similarity only\n"
            "- Ignore clothing, body size/shape differences (expected to differ)\n"
            "- Ignore background\n"
            "- Return only the numeric score, nothing else\n"
            "\n"
            "[OUTPUT FORMAT]\n"
            "A single integer between 1 and 10. Nothing else."
        ),
    },
    {
        "feature": "benchmarking",
        "version": "v1.0",
        "is_active": True,
        "prompt_text": (
            "[ROLE]\n"
            "You are a fitness data analyst for PRLifts.\n"
            "\n"
            "[CONTEXT]\n"
            "User profile:\n"
            "- Age: {age} (or 'not provided')\n"
            "- Gender: {gender} (or 'not provided')\n"
            "- Goal: {goal} (or 'not provided')\n"
            "\n"
            "Exercise: {exercise_name}\n"
            "User's personal record: {pr_value} {pr_unit}\n"
            "Record type: {record_type}\n"
            "\n"
            "[TASK]\n"
            "Provide a brief, accurate benchmark comparison for this personal record.\n"
            "Use established strength standards (e.g. ExRx, Symmetric Strength)"
            " appropriate\n"
            "for the user's age and gender if provided.\n"
            "\n"
            "[CONSTRAINTS]\n"
            "- Maximum 2 sentences\n"
            "- If age/gender not provided, note that comparison is approximate\n"
            "- Use encouraging but accurate framing\n"
            "- Never claim the user is in a specific percentile without data to"
            " support it\n"
            "- Frame as 'relative to general population' not 'compared to other"
            " users'\n"
            "- Never give medical advice\n"
            "\n"
            "[OUTPUT FORMAT]\n"
            "Plain text only. 2 sentences maximum."
        ),
    },
]

# ---------------------------------------------------------------------------
# Database upsert
# ---------------------------------------------------------------------------

# Targets the partial unique index idx_one_active_per_feature defined as:
#   CREATE UNIQUE INDEX idx_one_active_per_feature
#       ON prompt_template (feature) WHERE is_active = TRUE
#
# When an active template for the feature already exists the DO UPDATE clause
# refreshes version and prompt_text in-place. When none exists, a new row is
# inserted. Either way the result is exactly one active template per feature.
_UPSERT_SQL = """
    INSERT INTO prompt_template (feature, version, prompt_text, is_active)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (feature) WHERE is_active = TRUE
    DO UPDATE SET
        version     = EXCLUDED.version,
        prompt_text = EXCLUDED.prompt_text
"""


async def upsert_prompts(
    conn: asyncpg.Connection,
    templates: list[dict[str, Any]],
) -> int:
    """
    Upserts prompt template records into the database.

    Safe to call multiple times — existing active templates for each feature
    are updated in-place rather than duplicated.

    Args:
        conn: Open asyncpg connection.
        templates: List of template dicts, each with feature, version,
            prompt_text, and is_active keys.

    Returns:
        Number of rows processed.
    """
    params = [
        (t["feature"], t["version"], t["prompt_text"], t["is_active"])
        for t in templates
    ]
    await conn.executemany(_UPSERT_SQL, params)
    return len(params)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    """
    Seeds the three initial PromptTemplate records into the database.

    Reads DATABASE_URL from .env.local then the environment.
    Exits with code 1 if DATABASE_URL is missing.
    """
    load_dotenv(".env.local")
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        stream=sys.stdout,
    )

    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        logger.error("DATABASE_URL is not set. Aborting.")
        sys.exit(1)

    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    conn = await asyncpg.connect(dsn)
    try:
        count = await upsert_prompts(conn, PROMPT_TEMPLATES)
        logger.info("Done. Upserted %d prompt templates.", count)
        for t in PROMPT_TEMPLATES:
            logger.info(
                "  %s %s (is_active=%s)", t["feature"], t["version"], t["is_active"]
            )
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
