"""
test_schema_mapping.py
PRLifts Backend Tests

Schema consistency CI tests. Validates that SchemaMapping.swift in PRLiftsCore
accurately mirrors the [iOS]/[BE] annotations declared in docs/SCHEMA.md.

Five test cases enforced:
  1. Every [iOS]-annotated column has a mapping entry in SchemaMapping.swift.
  2. Every swiftProperty in SchemaMapping.swift is lowerCamelCase.
  3. Every swiftType in SchemaMapping.swift is compatible with the PostgreSQL type.
  4. No [BE]-annotated column appears in SchemaMapping.swift.
  5. Every column in SCHEMA.md carries an [iOS] or [BE] annotation.
"""

import pytest

from scripts.validate_schema_mapping import (
    ColumnInfo,
    MappingEntry,
    is_lower_camel_case,
    is_type_compatible,
    parse_schema_mapping_swift,
    parse_schema_md,
)


@pytest.fixture(scope="module")
def schema_data() -> tuple[list[ColumnInfo], list[tuple[str, str]]]:
    return parse_schema_md()


@pytest.fixture(scope="module")
def mapping_entries() -> list[MappingEntry]:
    return parse_schema_mapping_swift()


def test_all_ios_columns_have_mapping(
    schema_data: tuple[list[ColumnInfo], list[tuple[str, str]]],
    mapping_entries: list[MappingEntry],
) -> None:
    """Every [iOS]-annotated column in SCHEMA.md must appear in SchemaMapping.swift."""
    annotated, _ = schema_data
    ios_pairs = {(c.table, c.pg_column) for c in annotated if c.annotation == "iOS"}
    mapped_pairs = {(e.table, e.pg_column) for e in mapping_entries}
    missing = ios_pairs - mapped_pairs
    assert not missing, "[iOS] columns missing from SchemaMapping.swift:\n" + "\n".join(
        f"  {t}.{c}" for t, c in sorted(missing)
    )


def test_swift_property_names_are_camel_case(
    mapping_entries: list[MappingEntry],
) -> None:
    """Every swiftProperty in SchemaMapping.swift must be lowerCamelCase."""
    violations = [
        (e.table, e.pg_column, e.swift_property)
        for e in mapping_entries
        if not is_lower_camel_case(e.swift_property)
    ]
    assert not violations, (
        "swiftProperty names that are not lowerCamelCase:\n"
        + "\n".join(f"  {t}.{p} -> '{s}'" for t, p, s in violations)
    )


def test_swift_types_are_compatible(
    schema_data: tuple[list[ColumnInfo], list[tuple[str, str]]],
    mapping_entries: list[MappingEntry],
) -> None:
    """Every swiftType in SchemaMapping.swift must be compatible with its pg type."""
    annotated, _ = schema_data
    pg_type_for = {(c.table, c.pg_column): c.pg_type for c in annotated}

    def _entry_pg_type(e: MappingEntry) -> str:
        return pg_type_for.get((e.table, e.pg_column), e.pg_type)

    violations = [
        (e.table, e.pg_column, _entry_pg_type(e), e.swift_type)
        for e in mapping_entries
        if not is_type_compatible(_entry_pg_type(e), e.swift_type)
    ]
    assert not violations, (
        "Type incompatibilities in SchemaMapping.swift:\n"
        + "\n".join(
            f"  {t}.{c}: pg={pt!r} incompatible with swift={st!r}"
            for t, c, pt, st in violations
        )
    )


def test_no_be_columns_in_mapping(
    schema_data: tuple[list[ColumnInfo], list[tuple[str, str]]],
    mapping_entries: list[MappingEntry],
) -> None:
    """No [BE]-annotated column from SCHEMA.md may appear in SchemaMapping.swift."""
    annotated, _ = schema_data
    be_pairs = {(c.table, c.pg_column) for c in annotated if c.annotation == "BE"}
    mapped_pairs = {(e.table, e.pg_column) for e in mapping_entries}
    violations = be_pairs & mapped_pairs
    assert not violations, (
        "[BE] columns that must not appear in SchemaMapping.swift:\n"
        + "\n".join(f"  {t}.{c}" for t, c in sorted(violations))
    )


def test_all_columns_are_annotated(
    schema_data: tuple[list[ColumnInfo], list[tuple[str, str]]],
) -> None:
    """Every column in SCHEMA.md must carry an [iOS] or [BE] annotation."""
    _, unannotated = schema_data
    assert not unannotated, (
        "Columns in SCHEMA.md without [iOS] or [BE] annotation:\n"
        + "\n".join(f"  {t}.{c}" for t, c in unannotated)
    )
