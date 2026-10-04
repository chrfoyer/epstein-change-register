"""Cheap guards against merge accidents that CI otherwise cannot see."""

import re
import subprocess
from pathlib import Path

import duckdb

ROOT = Path(__file__).parent.parent
TEXT_SUFFIXES = {".md", ".py", ".json", ".yml", ".yaml", ".toml", ".html", ".csv"}
CONFLICT = re.compile(r"^(<{7}( |$)|={7}$|>{7}( |$))", re.MULTILINE)


def tracked_text_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [ROOT / p for p in out.stdout.splitlines() if (ROOT / p).suffix in TEXT_SUFFIXES]


def test_no_merge_conflict_markers():
    offenders = [
        p.relative_to(ROOT).as_posix()
        for p in tracked_text_files()
        if p.exists() and CONFLICT.search(p.read_text(encoding="utf-8", errors="replace"))
    ]
    assert offenders == []


def test_decision_ids_are_unique_and_ascending():
    """A botched rebase can delete or duplicate an entry; the log must stay intact.
    Gaps (e.g., D-015 reserved but unused) are expected and allowed."""
    text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
    ids = [int(m) for m in re.findall(r"^## D-(\d{3}) ", text, re.MULTILINE)]
    # Filter out placeholder "D-00N" entries
    ids = [d for d in ids if d > 0]
    assert ids == sorted(set(ids)), f"decision ids not unique or out of order: {ids}"
    assert ids[0] == 1, f"first decision should be D-001, got D-{ids[0]:03d}"


def test_decision_references_exist():
    """All D-NNN references in source code must exist in DECISIONS.md.
    Docs are excluded (they may contain forward-looking references to planned decisions)."""
    decisions_text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
    existing_ids = set(int(m) for m in re.findall(r"^## D-(\d{3}) ", decisions_text, re.MULTILINE))

    # Scan Python source code for D-NNN references
    # Docs are excluded since they may reference pending decisions (D-017, D-018, etc.)
    referenced_ids = set()
    for p in (ROOT / "src").glob("**/*.py"):
        text = p.read_text(encoding="utf-8", errors="replace")
        referenced_ids.update(int(m) for m in re.findall(r"\bD-(\d{3})\b", text))

    orphaned = referenced_ids - existing_ids
    assert orphaned == set(), f"source code references non-existent decisions: {sorted(orphaned)}"


def test_table_schemas_exist_and_match():
    """Verify that tables defined in contract.py and store.py actually exist in DuckDB."""
    from register import contract, store

    con = store.connect(":memory:")

    # Check listing_capture table
    con.execute(contract.LISTING_CAPTURE_DDL)
    actual_capture = tuple(
        (name, dtype) for name, dtype in con.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'listing_capture' ORDER BY ordinal_position"
        ).fetchall()
    )
    assert actual_capture == contract.LISTING_CAPTURE_COLUMNS, (
        f"listing_capture schema mismatch: {actual_capture} != {contract.LISTING_CAPTURE_COLUMNS}"
    )

    # Check listing_capture_file table
    con.execute(contract.LISTING_CAPTURE_FILE_DDL)
    actual_files = tuple(
        (name, dtype) for name, dtype in con.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'listing_capture_file' ORDER BY ordinal_position"
        ).fetchall()
    )
    assert actual_files == contract.LISTING_CAPTURE_FILE_COLUMNS, (
        f"listing_capture_file schema mismatch: {actual_files} != {contract.LISTING_CAPTURE_FILE_COLUMNS}"
    )
