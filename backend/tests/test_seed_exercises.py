"""
test_seed_exercises.py
PRLifts Backend Tests

Unit tests for the field-mapping logic in scripts/seed_exercises.py.
All functions under test are pure (no I/O), so no mocking or database
connection is required for the unit test portion.

Integration tests at the bottom require a real database with exercises
already seeded and are skipped automatically when ENVIRONMENT=test.
Run locally with:
    ENVIRONMENT=development pytest tests/test_seed_exercises.py -v
"""

import os
from typing import Any

import pytest

_REAL_DB_AVAILABLE = os.environ.get("ENVIRONMENT") != "test"

# ---------------------------------------------------------------------------
# map_muscle_group
# ---------------------------------------------------------------------------


def test_map_muscle_group_target_override_takes_precedence_over_body_part() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_muscle_group

    result = map_muscle_group("chest", "pectorals")

    # Assert — "pectorals" is in TARGET_OVERRIDES; bodyPart "chest" is irrelevant
    assert result == "mid_chest"


def test_map_muscle_group_uses_body_part_when_target_is_unmapped() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_muscle_group

    result = map_muscle_group("back", "unknown_target_value")

    # Assert — falls back to BODY_PART_MAP["back"]
    assert result == "upper_back"


def test_map_muscle_group_falls_back_to_full_body_when_both_unmapped() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_muscle_group

    result = map_muscle_group("unknown_part", "unknown_target")

    # Assert
    assert result == "full_body"


def test_map_muscle_group_maps_waist_body_part_to_abs() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_muscle_group

    result = map_muscle_group("waist", "")

    # Assert
    assert result == "abs"


def test_map_muscle_group_target_lower_back_maps_to_lower_back() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_muscle_group

    result = map_muscle_group("back", "lower back")

    # Assert
    assert result == "lower_back"


def test_map_muscle_group_is_case_insensitive() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_muscle_group

    result = map_muscle_group("CHEST", "Pectorals")

    # Assert
    assert result == "mid_chest"


# ---------------------------------------------------------------------------
# map_secondary_muscles
# ---------------------------------------------------------------------------


def test_map_secondary_muscles_returns_mapped_values() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_secondary_muscles

    result = map_secondary_muscles(["triceps", "forearms"])

    # Assert
    assert result == ["triceps", "biceps"]


def test_map_secondary_muscles_drops_unmapped_values() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_secondary_muscles

    result = map_secondary_muscles(["triceps", "unknown_muscle"])

    # Assert — unmapped entry silently dropped
    assert result == ["triceps"]


def test_map_secondary_muscles_returns_empty_list_for_empty_input() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_secondary_muscles

    result = map_secondary_muscles([])

    # Assert
    assert result == []


def test_map_secondary_muscles_returns_empty_list_when_all_unmapped() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_secondary_muscles

    result = map_secondary_muscles(["completely_unknown", "also_unknown"])

    # Assert
    assert result == []


# ---------------------------------------------------------------------------
# map_equipment
# ---------------------------------------------------------------------------


def test_map_equipment_maps_body_weight_to_bodyweight() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_equipment

    result = map_equipment("body weight")

    # Assert
    assert result == "bodyweight"


def test_map_equipment_maps_leverage_machine_to_machine() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_equipment

    result = map_equipment("leverage machine")

    # Assert
    assert result == "machine"


def test_map_equipment_maps_ez_barbell_to_barbell() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_equipment

    result = map_equipment("ez barbell")

    # Assert
    assert result == "barbell"


def test_map_equipment_maps_stationary_bike_to_cardio_machine() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_equipment

    result = map_equipment("stationary bike")

    # Assert
    assert result == "cardio_machine"


def test_map_equipment_falls_back_to_other_for_unknown_equipment() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_equipment

    result = map_equipment("some_unknown_equipment")

    # Assert
    assert result == "other"


def test_map_equipment_is_case_insensitive() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_equipment

    result = map_equipment("Barbell")

    # Assert
    assert result == "barbell"


# ---------------------------------------------------------------------------
# map_category
# ---------------------------------------------------------------------------


def test_map_category_returns_cardio_for_cardio_body_part() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_category

    result = map_category("cardio", "barbell")

    # Assert — bodyPart takes precedence
    assert result == "cardio"


def test_map_category_returns_bodyweight_for_bodyweight_equipment() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_category

    result = map_category("chest", "bodyweight")

    # Assert
    assert result == "bodyweight"


def test_map_category_returns_strength_as_default() -> None:
    # Arrange + Act
    from scripts.seed_exercises import map_category

    result = map_category("chest", "barbell")

    # Assert
    assert result == "strength"


def test_map_category_cardio_body_part_overrides_bodyweight_equipment() -> None:
    # Arrange + Act — an unusual but possible combination
    from scripts.seed_exercises import map_category

    result = map_category("cardio", "bodyweight")

    # Assert — cardio body part wins
    assert result == "cardio"


# ---------------------------------------------------------------------------
# transform_exercise
# ---------------------------------------------------------------------------


_MISSING = object()  # sentinel distinct from None and []


def _edb_fixture(
    name: str = "Bench Press",
    body_part: str = "chest",
    target: str = "pectorals",
    equipment: str = "barbell",
    secondary_muscles: list[str] | None = None,
    instructions: object = _MISSING,
    gif_url: str = "https://example.com/bench.gif",
) -> dict[str, Any]:
    return {
        "id": "0001",
        "name": name,
        "bodyPart": body_part,
        "target": target,
        "equipment": equipment,
        "secondaryMuscles": (
            secondary_muscles
            if secondary_muscles is not None
            else ["triceps", "shoulders"]
        ),
        "instructions": (
            instructions if instructions is not _MISSING else ["Lie flat.", "Press up."]
        ),
        "gifUrl": gif_url,
    }


def test_transform_exercise_returns_complete_dict_for_valid_record() -> None:
    # Arrange
    from scripts.seed_exercises import transform_exercise

    raw = _edb_fixture()

    # Act
    result = transform_exercise(raw)

    # Assert
    assert result is not None
    assert result["name"] == "Bench Press"
    assert result["category"] == "strength"
    assert result["muscle_group"] == "mid_chest"
    assert result["equipment"] == "barbell"
    assert isinstance(result["secondary_muscle_groups"], list)
    assert "Lie flat." in result["instructions"]
    assert result["demo_url"] == "https://example.com/bench.gif"


def test_transform_exercise_joins_instructions_with_newline() -> None:
    # Arrange
    from scripts.seed_exercises import transform_exercise

    raw = _edb_fixture(instructions=["Step one.", "Step two.", "Step three."])

    # Act
    result = transform_exercise(raw)

    # Assert
    assert result is not None
    assert result["instructions"] == "Step one.\nStep two.\nStep three."


def test_transform_exercise_titlecases_name() -> None:
    # Arrange
    from scripts.seed_exercises import transform_exercise

    raw = _edb_fixture(name="bench press")

    # Act
    result = transform_exercise(raw)

    # Assert
    assert result is not None
    assert result["name"] == "Bench Press"


def test_transform_exercise_returns_none_for_empty_name() -> None:
    # Arrange
    from scripts.seed_exercises import transform_exercise

    raw = _edb_fixture(name="")

    # Act
    result = transform_exercise(raw)

    # Assert
    assert result is None


def test_transform_exercise_returns_none_for_whitespace_only_name() -> None:
    # Arrange
    from scripts.seed_exercises import transform_exercise

    raw = _edb_fixture(name="   ")

    # Act
    result = transform_exercise(raw)

    # Assert
    assert result is None


def test_transform_exercise_sets_none_for_missing_instructions() -> None:
    # Arrange
    from scripts.seed_exercises import transform_exercise

    raw = _edb_fixture(instructions=[])

    # Act
    result = transform_exercise(raw)

    # Assert
    assert result is not None
    assert result["instructions"] is None


def test_transform_exercise_sets_none_for_missing_gif_url() -> None:
    # Arrange
    from scripts.seed_exercises import transform_exercise

    raw = _edb_fixture(gif_url="")

    # Act
    result = transform_exercise(raw)

    # Assert
    assert result is not None
    assert result["demo_url"] is None


def test_transform_exercise_cardio_exercise_maps_to_cardio_category() -> None:
    # Arrange
    from scripts.seed_exercises import transform_exercise

    raw = _edb_fixture(
        name="Treadmill Run",
        body_part="cardio",
        target="cardiovascular system",
        equipment="stationary bike",
    )

    # Act
    result = transform_exercise(raw)

    # Assert
    assert result is not None
    assert result["category"] == "cardio"
    assert result["equipment"] == "cardio_machine"


def test_transform_exercise_bodyweight_exercise_maps_to_bodyweight_category() -> None:
    # Arrange
    from scripts.seed_exercises import transform_exercise

    raw = _edb_fixture(
        name="Pull-Up",
        body_part="back",
        target="lats",
        equipment="body weight",
        secondary_muscles=[],
    )

    # Act
    result = transform_exercise(raw)

    # Assert
    assert result is not None
    assert result["category"] == "bodyweight"
    assert result["muscle_group"] == "upper_back"
    assert result["equipment"] == "bodyweight"


# ---------------------------------------------------------------------------
# Integration tests — skipped when ENVIRONMENT=test
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _REAL_DB_AVAILABLE,
    reason=(
        "Integration test — requires a real database with exercises seeded. "
        "Run with ENVIRONMENT=development after executing seed_exercises.py."
    ),
)
async def test_exercise_count_is_greater_than_zero_after_seed() -> None:
    """Verifies the exercise table is non-empty after the seed script runs."""
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
        count: int = await conn.fetchval(
            "SELECT COUNT(*) FROM exercise WHERE is_custom = false"
        )
    finally:
        await conn.close()

    # Assert
    assert count > 0, f"Expected exercises in the database, found {count}"


@pytest.mark.skipif(
    not _REAL_DB_AVAILABLE,
    reason=(
        "Integration test — requires a real database with exercises seeded. "
        "Run with ENVIRONMENT=development after executing seed_exercises.py."
    ),
)
async def test_known_exercise_is_retrievable_by_name_after_seed() -> None:
    """Verifies that 'Bench Press' exists and has expected fields after seeding."""
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
        row = await conn.fetchrow(
            "SELECT name, category, muscle_group, equipment "
            "FROM exercise WHERE name = 'Bench Press'"
        )
    finally:
        await conn.close()

    # Assert
    assert row is not None, "Bench Press not found — has the seed script been run?"
    assert row["category"] == "strength"
    assert row["muscle_group"] == "mid_chest"
    assert row["equipment"] == "barbell"
