#!/usr/bin/env python3
"""
seed_exercises.py
PRLifts Backend — Scripts

Fetches all exercises from ExerciseDB (via RapidAPI) and upserts them into
the PRLifts exercise table. Idempotent — uses INSERT ... ON CONFLICT (name)
DO UPDATE, so re-running updates existing exercises without creating duplicates.

Usage (from backend/):
    python scripts/seed_exercises.py

Environment variables required (read from environment or .env.local):
    EXERCISEDB_API_KEY   RapidAPI key for ExerciseDB
    DATABASE_URL         asyncpg connection string (postgresql+asyncpg://...)

See docs/SEED_DATA.md for the complete field-mapping specification.
"""

import asyncio
import logging
import os
import sys
from typing import Any

import asyncpg
import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_EDB_HOST = "edb-with-videos-and-images-by-ascendapi.p.rapidapi.com"
_PAGE_SIZE = 100

# ---------------------------------------------------------------------------
# Field mapping tables — copied verbatim from docs/SEED_DATA.md
# ---------------------------------------------------------------------------

BODY_PART_MAP: dict[str, str] = {
    "chest": "mid_chest",
    "back": "upper_back",
    "shoulders": "shoulders",
    "upper arms": "biceps",
    "lower arms": "biceps",
    "upper legs": "quads",
    "lower legs": "calves",
    "waist": "abs",
    "cardio": "full_body",
    "neck": "full_body",
}

TARGET_OVERRIDES: dict[str, str] = {
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

EQUIPMENT_MAP: dict[str, str] = {
    "barbell": "barbell",
    "dumbbell": "dumbbell",
    "kettlebell": "kettlebell",
    "cable": "cable",
    "machine": "machine",
    "leverage machine": "machine",
    "smith machine": "machine",
    "body weight": "bodyweight",
    "assisted": "bodyweight",
    "band": "other",
    "roller": "other",
    "rope": "other",
    "stability ball": "other",
    "tire": "other",
    "trap bar": "barbell",
    "weighted": "other",
    "ez barbell": "barbell",
    "olympic barbell": "barbell",
    "hammer": "other",
    "sled machine": "machine",
    "stationary bike": "cardio_machine",
    "skierg machine": "cardio_machine",
    "upper body ergometer": "cardio_machine",
}

# ---------------------------------------------------------------------------
# Pure mapping functions (no I/O — easily unit-tested)
# ---------------------------------------------------------------------------


def map_muscle_group(body_part: str, target: str) -> str:
    """
    Maps EDB bodyPart + target to a PRLifts muscle_group enum value.

    TARGET_OVERRIDES take precedence over BODY_PART_MAP. Falls back to
    'full_body' so no exercise is dropped for an unmapped muscle.

    Args:
        body_part: EDB bodyPart field value.
        target: EDB target field value.

    Returns:
        A valid muscle_group enum string.
    """
    override = TARGET_OVERRIDES.get(target.lower())
    if override:
        return override
    return BODY_PART_MAP.get(body_part.lower(), "full_body")


def map_secondary_muscles(secondaries: list[str]) -> list[str]:
    """
    Maps an EDB secondaryMuscles array to PRLifts muscle_group enum values.

    Unmapped values are silently dropped — secondary muscles are informational
    and a partial list is better than failing the import.

    Args:
        secondaries: List of EDB secondary muscle strings.

    Returns:
        List of valid muscle_group enum strings (may be empty).
    """
    result = []
    for muscle in secondaries:
        mapped = TARGET_OVERRIDES.get(muscle.lower())
        if mapped:
            result.append(mapped)
    return result


def map_equipment(equipment: str) -> str:
    """
    Maps an EDB equipment string to a PRLifts exercise_equipment enum value.

    Falls back to 'other' rather than skipping the exercise.

    Args:
        equipment: EDB equipment field value.

    Returns:
        A valid exercise_equipment enum string.
    """
    return EQUIPMENT_MAP.get(equipment.lower(), "other")


def map_category(body_part: str, equipment_mapped: str) -> str:
    """
    Derives the PRLifts exercise_category from EDB bodyPart and mapped equipment.

    Args:
        body_part: EDB bodyPart field value (raw, not yet mapped).
        equipment_mapped: Already-mapped PRLifts equipment string.

    Returns:
        A valid exercise_category enum string.
    """
    if body_part.lower() == "cardio":
        return "cardio"
    if equipment_mapped == "bodyweight":
        return "bodyweight"
    return "strength"


def transform_exercise(raw: dict[str, Any]) -> dict[str, Any] | None:
    """
    Transforms a single EDB exercise record into PRLifts exercise table format.

    Returns None only when the exercise has an empty name — all other fields
    have safe fallbacks. Callers should count and log skipped exercises.

    Args:
        raw: EDB exercise dict from the API response.

    Returns:
        Dict ready for database upsert, or None to skip the exercise.
    """
    name = (raw.get("name") or "").strip().title()
    if not name:
        logger.warning("Skipping exercise with empty name: %s", raw.get("id", "?"))
        return None

    body_part: str = raw.get("bodyPart") or ""
    target: str = raw.get("target") or ""
    equipment_raw: str = raw.get("equipment") or ""
    secondary_raw: list[str] = raw.get("secondaryMuscles") or []
    instructions_raw: list[str] = raw.get("instructions") or []

    equipment_mapped = map_equipment(equipment_raw)
    muscle = map_muscle_group(body_part, target)
    secondary = map_secondary_muscles(secondary_raw)
    category = map_category(body_part, equipment_mapped)
    instructions = "\n".join(instructions_raw) if instructions_raw else None
    demo_url: str | None = raw.get("gifUrl") or None

    return {
        "name": name,
        "category": category,
        "muscle_group": muscle,
        "secondary_muscle_groups": secondary,
        "equipment": equipment_mapped,
        "instructions": instructions,
        "demo_url": demo_url,
    }


# ---------------------------------------------------------------------------
# I/O — fetching and upserting
# ---------------------------------------------------------------------------


async def fetch_all_exercises(api_key: str) -> list[dict[str, Any]]:
    """
    Fetches all exercises from ExerciseDB via paginated GET /exercises calls.

    Args:
        api_key: RapidAPI key for the ExerciseDB host.

    Returns:
        List of raw EDB exercise dicts.

    Raises:
        httpx.HTTPStatusError: On non-2xx response.
        httpx.TimeoutException: On request timeout.
    """
    all_exercises: list[dict[str, Any]] = []
    offset = 0
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": _EDB_HOST,
    }
    base_url = f"https://{_EDB_HOST}/exercises"

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            response = await client.get(
                base_url,
                headers=headers,
                params={"limit": _PAGE_SIZE, "offset": offset},
            )
            response.raise_for_status()
            batch: list[dict[str, Any]] = response.json()
            if not batch:
                break
            all_exercises.extend(batch)
            logger.info(
                "Fetched %d exercises so far (offset %d)",
                len(all_exercises),
                offset,
            )
            if len(batch) < _PAGE_SIZE:
                break
            offset += _PAGE_SIZE

    return all_exercises


# The ::text[]::muscle_group[] double-cast is required because asyncpg sends
# Python lists as a generic array; the first cast pins the element type to
# text so PostgreSQL can coerce each element to the muscle_group enum.
_UPSERT_SQL = """
    INSERT INTO exercise (
        name, category, muscle_group, secondary_muscle_groups,
        equipment, instructions, demo_url, is_custom, created_by
    ) VALUES (
        $1,
        $2::exercise_category,
        $3::muscle_group,
        $4::text[]::muscle_group[],
        $5::exercise_equipment,
        $6,
        $7,
        false,
        null
    )
    ON CONFLICT (name) DO UPDATE SET
        category              = EXCLUDED.category,
        muscle_group          = EXCLUDED.muscle_group,
        secondary_muscle_groups = EXCLUDED.secondary_muscle_groups,
        equipment             = EXCLUDED.equipment,
        instructions          = EXCLUDED.instructions,
        demo_url              = EXCLUDED.demo_url,
        updated_at            = NOW()
"""


async def upsert_exercises(
    conn: asyncpg.Connection,
    records: list[dict[str, Any]],
) -> int:
    """
    Upserts transformed exercises into the database in a single transaction.

    Uses INSERT ... ON CONFLICT (name) DO UPDATE — idempotent on re-run.

    Args:
        conn: Open asyncpg connection.
        records: Transformed exercise dicts from transform_exercise().

    Returns:
        Number of rows processed.
    """
    params = [
        (
            r["name"],
            r["category"],
            r["muscle_group"],
            r["secondary_muscle_groups"],
            r["equipment"],
            r["instructions"],
            r["demo_url"],
        )
        for r in records
    ]
    await conn.executemany(_UPSERT_SQL, params)
    return len(params)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    """
    Orchestrates the full seed run: fetch → transform → upsert.

    Reads EXERCISEDB_API_KEY and DATABASE_URL from .env.local then environment.
    Exits with code 1 if either variable is missing.
    """
    load_dotenv(".env.local")
    load_dotenv()  # fallback: plain .env

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        stream=sys.stdout,
    )

    api_key = os.environ.get("EXERCISEDB_API_KEY", "")
    if not api_key:
        logger.error("EXERCISEDB_API_KEY is not set. Aborting.")
        sys.exit(1)

    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        logger.error("DATABASE_URL is not set. Aborting.")
        sys.exit(1)

    # asyncpg uses postgresql:// — strip the SQLAlchemy dialect prefix if present
    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    logger.info("Fetching exercises from ExerciseDB...")
    raw_exercises = await fetch_all_exercises(api_key)
    logger.info("Fetched %d raw exercises from ExerciseDB.", len(raw_exercises))

    transformed: list[dict[str, Any]] = []
    skipped = 0
    for raw in raw_exercises:
        record = transform_exercise(raw)
        if record is None:
            skipped += 1
        else:
            transformed.append(record)

    logger.info(
        "Transformation complete: %d exercises ready, %d skipped.",
        len(transformed),
        skipped,
    )

    conn = await asyncpg.connect(dsn)
    try:
        upserted = await upsert_exercises(conn, transformed)
        logger.info("Done. Upserted %d exercises into the database.", upserted)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
