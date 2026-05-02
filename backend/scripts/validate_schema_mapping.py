"""
validate_schema_mapping.py
PRLifts Backend

Parses docs/SCHEMA.md [iOS]/[BE] column annotations and validates the
declarative mapping in PRLiftsCore/Sources/PRLiftsCore/Models/SchemaMapping.swift.

Imported by tests/test_schema_mapping.py — not a standalone script.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_MD_PATH = REPO_ROOT / "docs" / "SCHEMA.md"
SCHEMA_MAPPING_SWIFT_PATH = (
    REPO_ROOT
    / "PRLiftsCore"
    / "Sources"
    / "PRLiftsCore"
    / "Models"
    / "SchemaMapping.swift"
)

_SQL_CONSTRAINT_KEYWORDS = frozenset(
    {"CONSTRAINT", "CHECK", "UNIQUE", "PRIMARY", "FOREIGN", "INDEX", "KEY"}
)

# Standard PostgreSQL type -> accepted Swift types.
# UUID may also map to a SwiftData relationship (checked separately).
_PG_SWIFT_COMPAT: dict[str, frozenset[str]] = {
    "UUID": frozenset({"UUID", "UUID?"}),
    "TEXT": frozenset({"String", "String?"}),
    "BOOLEAN": frozenset({"Bool", "Bool?"}),
    "INTEGER": frozenset({"Int", "Int?"}),
    "SMALLINT": frozenset({"Int", "Int?"}),
    "NUMERIC": frozenset({"Double", "Double?", "Decimal", "Decimal?"}),
    "TIMESTAMPTZ": frozenset({"Date", "Date?"}),
    "DATE": frozenset({"Date", "Date?"}),
    "JSONB": frozenset({"String", "String?", "Data", "Data?"}),
}


class ColumnInfo(NamedTuple):
    table: str
    pg_column: str
    pg_type: str
    annotation: str  # 'iOS' or 'BE'


class MappingEntry(NamedTuple):
    table: str
    pg_column: str
    pg_type: str
    swift_model: str
    swift_property: str
    swift_type: str


def _normalize_pg_type(raw: str) -> str:
    """Strip NUMERIC(n,m) params; uppercase standard types; preserve enums/arrays."""
    base = re.sub(r"\(.*?\)", "", raw).strip().rstrip(",")
    return base.upper() if base.upper() in _PG_SWIFT_COMPAT else base


def parse_schema_md(
    path: Path = SCHEMA_MD_PATH,
) -> tuple[list[ColumnInfo], list[tuple[str, str]]]:
    """
    Parse SCHEMA.md and return annotated columns and unannotated column names.

    Returns:
        annotated: all columns carrying an [iOS] or [BE] annotation.
        unannotated: (table, column) pairs that lack any annotation.
    """
    content = path.read_text(encoding="utf-8")
    sql_blocks = re.findall(r"```sql\n(.*?)```", content, re.DOTALL)

    annotated: list[ColumnInfo] = []
    unannotated: list[tuple[str, str]] = []

    table_re = re.compile(r'CREATE TABLE\s+"?(\w+)"?\s*\((.*?)\);', re.DOTALL)

    for block in sql_blocks:
        for table_match in table_re.finditer(block):
            table_name = table_match.group(1)
            body = table_match.group(2)

            depth = 0
            for line in body.splitlines():
                # Lines at depth > 0 are inside a CONSTRAINT body — not column defs.
                if depth > 0:
                    depth += line.count("(") - line.count(")")
                    continue

                col_match = re.match(r"^\s+(\w+)\s+(\S+)", line)
                if not col_match:
                    continue
                col_name = col_match.group(1)
                if col_name.upper() in _SQL_CONSTRAINT_KEYWORDS:
                    # Track paren depth so subsequent lines inside the constraint
                    # body (e.g. multi-line CHECK) are skipped.
                    depth += line.count("(") - line.count(")")
                    continue

                raw_type = col_match.group(2).rstrip(",")
                pg_type = _normalize_pg_type(raw_type)
                ann_match = re.search(r"--\s*\[(iOS|BE)\]", line)
                if ann_match:
                    annotated.append(
                        ColumnInfo(table_name, col_name, pg_type, ann_match.group(1))
                    )
                else:
                    unannotated.append((table_name, col_name))

    return annotated, unannotated


def parse_schema_mapping_swift(
    path: Path = SCHEMA_MAPPING_SWIFT_PATH,
) -> list[MappingEntry]:
    """Parse SchemaMapping.swift and return all declared Column mapping entries."""
    content = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'Column\(\s*table:\s*"([^"]+)",\s*pgColumn:\s*"([^"]+)",\s*'
        r'pgType:\s*"([^"]+)",\s*swiftModel:\s*"([^"]+)",\s*'
        r'swiftProperty:\s*"([^"]+)",\s*swiftType:\s*"([^"]+)"\s*\)',
        re.DOTALL,
    )
    return [
        MappingEntry(
            m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)
        )
        for m in pattern.finditer(content)
    ]


def is_lower_camel_case(name: str) -> bool:
    """Return True if name is a valid lowerCamelCase Swift property name."""
    return bool(name) and not name[0].isupper() and "_" not in name


def is_type_compatible(pg_type: str, swift_type: str) -> bool:
    """Return True if swift_type is a valid Swift representation of pg_type."""
    # Array columns: pg ends with '[]', Swift must be an array literal '[...]'
    if pg_type.endswith("[]"):
        return swift_type.startswith("[")
    # Standard PostgreSQL types
    if pg_type in _PG_SWIFT_COMPAT:
        if swift_type in _PG_SWIFT_COMPAT[pg_type]:
            return True
        # UUID FK columns may map to SwiftData relationships (e.g. User?, Workout?)
        if pg_type == "UUID":
            base = swift_type.rstrip("?")
            return bool(re.match(r"^[A-Z][A-Za-z0-9]+$", base))
        return False
    # PostgreSQL enum types and other unknown types — accept any non-empty Swift type
    return bool(swift_type)
