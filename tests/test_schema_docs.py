"""Drift test: SCHEMA.md must match the actual DDL. If it disagrees, this fails."""

import re
from pathlib import Path

import duckdb
import pytest

from register import store


def parse_schema_md():
    """Extract documented table schemas from SCHEMA.md.

    Returns a dict mapping table name to list of (column, type) tuples.
    """
    schema_path = Path(__file__).parent.parent / "SCHEMA.md"
    content = schema_path.read_text()

    tables = {}
    current_table = None
    in_table = False

    for line in content.splitlines():
        # Detect "## Table: `table_name`"
        table_match = re.match(r'^## Table: `(\w+)`', line)
        if table_match:
            current_table = table_match.group(1)
            in_table = True
            tables[current_table] = []
            continue

        # Detect "## View: `view_name`" — skip views
        if re.match(r'^## View:', line):
            in_table = False
            continue

        # Detect section headings — stop processing current table
        if re.match(r'^##+ ', line):
            in_table = False
            continue

        # In a table, parse markdown row: | Column | Type | ...
        if in_table and current_table and line.startswith('|'):
            # Skip header rows (those with dashes)
            if re.search(r'[-]{2,}', line):
                continue
            # Skip separator lines and headers
            if 'Column' in line or 'Type' in line:
                continue

            # Parse: | `column_name` | Type | ...
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 4:  # Must have at least | col | type | ...
                col_name = parts[1].strip('` ')
                type_str = parts[2].strip('` ')

                # Skip empty rows
                if col_name and type_str:
                    # Map documented type names to DuckDB types
                    duckdb_type = _normalize_type(type_str)
                    if col_name and duckdb_type:
                        tables[current_table].append((col_name, duckdb_type))

    return tables


def _normalize_type(type_str):
    """Map documented type names to DuckDB column types."""
    type_str = type_str.upper().strip()
    # DuckDB uses uppercase, but allow common variations
    type_map = {
        'VARCHAR': 'VARCHAR',
        'INTEGER': 'INTEGER',
        'BIGINT': 'BIGINT',
        'BOOLEAN': 'BOOLEAN',
    }
    if type_str not in type_map:
        raise ValueError(f"Unknown type '{type_str}' in SCHEMA.md. Known types: {set(type_map.keys())}")
    return type_map[type_str]


def get_actual_schema(con, table_name):
    """Fetch actual schema from DuckDB for a table.

    Returns list of (column_name, data_type) tuples in ordinal order.
    """
    rows = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name = ? ORDER BY ordinal_position",
        [table_name]
    ).fetchall()
    return rows


def test_schema_md_documents_all_bronze_tables():
    """Every bronze table must be documented in SCHEMA.md."""
    documented = set(parse_schema_md().keys())

    # These are the bronze tables that must be documented (from store.py TABLES)
    required = {'analytics_fetch', 'analytics_file_observation', 'listing_capture', 'listing_capture_file'}

    missing = required - documented
    assert missing == set(), f"Tables not documented in SCHEMA.md: {missing}"


def test_schema_md_matches_analytics_fetch():
    """SCHEMA.md columns for analytics_fetch must match DDL."""
    con = store.connect(":memory:")
    documented = parse_schema_md().get('analytics_fetch', [])
    actual = get_actual_schema(con, 'analytics_fetch')

    _assert_columns_match('analytics_fetch', documented, actual)


def test_schema_md_matches_analytics_file_observation():
    """SCHEMA.md columns for analytics_file_observation must match DDL."""
    con = store.connect(":memory:")
    documented = parse_schema_md().get('analytics_file_observation', [])
    actual = get_actual_schema(con, 'analytics_file_observation')

    _assert_columns_match('analytics_file_observation', documented, actual)


def test_schema_md_matches_listing_capture():
    """SCHEMA.md columns for listing_capture must match DDL."""
    con = store.connect(":memory:")
    documented = parse_schema_md().get('listing_capture', [])
    actual = get_actual_schema(con, 'listing_capture')

    _assert_columns_match('listing_capture', documented, actual)


def test_schema_md_matches_listing_capture_file():
    """SCHEMA.md columns for listing_capture_file must match DDL."""
    con = store.connect(":memory:")
    documented = parse_schema_md().get('listing_capture_file', [])
    actual = get_actual_schema(con, 'listing_capture_file')

    _assert_columns_match('listing_capture_file', documented, actual)


def _assert_columns_match(table_name, documented, actual):
    """Assert that documented and actual columns match.

    Checks:
    - Same number of columns
    - Same column names in same order
    - Same types (after normalization)
    """
    doc_cols = [col for col, _ in documented]
    actual_cols = [col for col, _ in actual]

    assert len(documented) == len(actual), (
        f"{table_name}: column count mismatch. "
        f"Documented {len(documented)} columns: {doc_cols}. "
        f"Actual {len(actual)} columns: {actual_cols}."
    )

    assert doc_cols == actual_cols, (
        f"{table_name}: column name mismatch. "
        f"Documented: {doc_cols}. "
        f"Actual: {actual_cols}."
    )

    for (doc_col, doc_type), (actual_col, actual_type) in zip(documented, actual):
        assert doc_type == actual_type, (
            f"{table_name}.{doc_col}: type mismatch. "
            f"Documented: {doc_type}. Actual: {actual_type}."
        )
