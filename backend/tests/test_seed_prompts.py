"""
test_seed_prompts.py
PRLifts Backend Tests

Unit tests for the prompt template definitions in scripts/seed_prompts.py.
Because all behaviour is pure data (no mapping logic, no I/O), the unit
tests verify structural invariants: correct count, required fields, content
constraints from docs/STANDARDS.md § 8.2 and docs/SEED_DATA.md § 2.

The integration test at the bottom requires a real database with prompt
templates already seeded and is skipped automatically when ENVIRONMENT=test.
Run manually with:
    ENVIRONMENT=development pytest tests/test_seed_prompts.py -v
"""

import os

import pytest

_REAL_DB_AVAILABLE = os.environ.get("ENVIRONMENT") != "test"

_EXPECTED_FEATURES = {"insight", "future_self", "benchmarking"}

# ---------------------------------------------------------------------------
# Structural invariants
# ---------------------------------------------------------------------------


def test_prompt_templates_contains_exactly_three_entries() -> None:
    # Arrange + Act
    from scripts.seed_prompts import PROMPT_TEMPLATES

    # Assert
    assert len(PROMPT_TEMPLATES) == 3


def test_all_three_expected_features_are_present() -> None:
    # Arrange + Act
    from scripts.seed_prompts import PROMPT_TEMPLATES

    features = {t["feature"] for t in PROMPT_TEMPLATES}

    # Assert
    assert features == _EXPECTED_FEATURES


def test_each_feature_appears_exactly_once() -> None:
    # Arrange + Act
    from scripts.seed_prompts import PROMPT_TEMPLATES

    features = [t["feature"] for t in PROMPT_TEMPLATES]

    # Assert — no duplicates
    assert len(features) == len(set(features))


def test_all_templates_have_is_active_true() -> None:
    # Arrange + Act
    from scripts.seed_prompts import PROMPT_TEMPLATES

    # Assert
    for template in PROMPT_TEMPLATES:
        assert template["is_active"] is True, (
            f"Template '{template['feature']}' has is_active={template['is_active']}"
        )


def test_all_templates_have_version_v1_0() -> None:
    # Arrange + Act
    from scripts.seed_prompts import PROMPT_TEMPLATES

    # Assert
    for template in PROMPT_TEMPLATES:
        assert template["version"] == "v1.0", (
            f"Template '{template['feature']}' has version={template['version']!r}"
        )


def test_all_templates_have_non_empty_prompt_text() -> None:
    # Arrange + Act
    from scripts.seed_prompts import PROMPT_TEMPLATES

    # Assert
    for template in PROMPT_TEMPLATES:
        assert isinstance(template["prompt_text"], str)
        assert len(template["prompt_text"].strip()) > 0, (
            f"Template '{template['feature']}' has empty prompt_text"
        )


def test_all_templates_have_required_structural_sections() -> None:
    # Arrange + Act
    from scripts.seed_prompts import PROMPT_TEMPLATES

    required_sections = ["[ROLE]", "[TASK]", "[CONSTRAINTS]", "[OUTPUT FORMAT]"]

    # Assert — every prompt must have all four sections (STANDARDS.md § 8.2)
    for template in PROMPT_TEMPLATES:
        text = template["prompt_text"]
        for section in required_sections:
            assert section in text, (
                f"Template '{template['feature']}' is missing section {section!r}"
            )


# ---------------------------------------------------------------------------
# Content constraints (STANDARDS.md § 8.2 and ai_forbidden_phrases.txt)
# ---------------------------------------------------------------------------


def test_insight_prompt_contains_forbidden_phrase_constraint() -> None:
    # Arrange
    from scripts.seed_prompts import PROMPT_TEMPLATES

    insight = next(t for t in PROMPT_TEMPLATES if t["feature"] == "insight")

    # Assert — the insight prompt must explicitly forbid extreme body language
    # per docs/STANDARDS.md § 8.2 Prompt Engineering / Forbidden Phrases
    text = insight["prompt_text"]
    assert "lose weight" in text
    assert "burn fat" in text


def test_insight_prompt_constrains_output_to_two_sentences() -> None:
    # Arrange
    from scripts.seed_prompts import PROMPT_TEMPLATES

    insight = next(t for t in PROMPT_TEMPLATES if t["feature"] == "insight")

    # Assert
    assert "2 sentences" in insight["prompt_text"]


def test_future_self_prompt_targets_scoring_not_generation() -> None:
    # Arrange
    from scripts.seed_prompts import PROMPT_TEMPLATES

    future_self = next(t for t in PROMPT_TEMPLATES if t["feature"] == "future_self")

    # Assert — future_self prompt is for Claude vision scoring only;
    # the Fal.ai generation prompt is constructed in code (not stored here)
    text = future_self["prompt_text"]
    assert "score" in text.lower()
    assert "1 to 10" in text or "1 and 10" in text


def test_future_self_prompt_output_is_numeric_only() -> None:
    # Arrange
    from scripts.seed_prompts import PROMPT_TEMPLATES

    future_self = next(t for t in PROMPT_TEMPLATES if t["feature"] == "future_self")

    # Assert — output format must be a single integer, nothing else
    assert "integer" in future_self["prompt_text"].lower()


def test_benchmarking_prompt_forbids_specific_percentile_claims() -> None:
    # Arrange
    from scripts.seed_prompts import PROMPT_TEMPLATES

    benchmarking = next(t for t in PROMPT_TEMPLATES if t["feature"] == "benchmarking")

    # Assert — must not claim percentile without supporting data
    assert "percentile" in benchmarking["prompt_text"].lower()


def test_benchmarking_prompt_forbids_medical_advice() -> None:
    # Arrange
    from scripts.seed_prompts import PROMPT_TEMPLATES

    benchmarking = next(t for t in PROMPT_TEMPLATES if t["feature"] == "benchmarking")

    # Assert
    assert "medical advice" in benchmarking["prompt_text"].lower()


# ---------------------------------------------------------------------------
# Integration test — skipped when ENVIRONMENT=test
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _REAL_DB_AVAILABLE,
    reason=(
        "Integration test — requires a real database with prompts seeded. "
        "Run with ENVIRONMENT=development after executing seed_prompts.py."
    ),
)
async def test_all_three_templates_retrievable_by_feature_after_seed() -> None:
    """Verifies that all three active templates exist in the database."""
    # Arrange
    import asyncpg
    from dotenv import load_dotenv

    load_dotenv(".env.local")
    load_dotenv()

    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        pytest.skip("DATABASE_URL not set")

    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    # Act
    conn = await asyncpg.connect(dsn)
    try:
        rows = await conn.fetch(
            "SELECT feature, version, is_active FROM prompt_template"
            " WHERE is_active = TRUE ORDER BY feature"
        )
    finally:
        await conn.close()

    # Assert
    found_features = {row["feature"] for row in rows}
    assert found_features == _EXPECTED_FEATURES, (
        f"Expected features {_EXPECTED_FEATURES}, found {found_features}"
    )
    for row in rows:
        assert row["version"] == "v1.0"
        assert row["is_active"] is True
