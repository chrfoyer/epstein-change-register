import re
from pathlib import Path

import duckdb
import pytest

from register import contract, store

CAPTURE = {
    "run_id": "run-1",
    "capture_ts": "2026-01-01T00:00:00+00:00",
    "source_url": "https://web.archive.org/cdx/search/cdx",
    "listing_url": "https://example.invalid/listing",
    "archive_url": "https://web.archive.org/web/20260101000000/https://example.invalid/listing",
    "archive_ts": "2026-01-01T00:00:00+00:00",
    "status": "ok",
}
FILES = [
    {"file_url": "https://example.invalid/DataSet 9/EFTA90000001.pdf", "bates_id": "EFTA90000001",
     "dataset": "9", "archive_digest": "A" * 32},
    {"file_url": "https://example.invalid/DataSet 9/EFTA90000002.pdf", "bates_id": "EFTA90000002",
     "dataset": "9"},
]


def columns(con, table):
    rows = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name = ? ORDER BY ordinal_position", [table]).fetchall()
    return tuple(rows)


def test_tables_match_contract_exactly():
    con = store.connect(":memory:")
    assert columns(con, "listing_capture") == contract.LISTING_CAPTURE_COLUMNS
    assert columns(con, "listing_capture_file") == contract.LISTING_CAPTURE_FILE_COLUMNS


def test_append_round_trip_and_nullable_digest():
    con = store.connect(":memory:")
    store.append_listing_capture(con, CAPTURE, FILES)
    assert con.execute("SELECT status, row_count FROM listing_capture").fetchone() == ("ok", 2)
    digests = con.execute("SELECT archive_digest FROM listing_capture_file ORDER BY bates_id").fetchall()
    assert digests == [("A" * 32,), (None,)]


@pytest.mark.parametrize("status", ["blocked", "error", "empty", "partial"])
def test_non_ok_capture_cannot_carry_file_rows(status):
    con = store.connect(":memory:")
    with pytest.raises(ValueError):
        store.append_listing_capture(con, {**CAPTURE, "status": status}, FILES)
    store.append_listing_capture(con, {**CAPTURE, "status": status}, [])
    assert con.execute("SELECT count(*) FROM listing_capture_file").fetchone()[0] == 0


def test_status_is_validated_in_helper_and_in_the_table():
    con = store.connect(":memory:")
    with pytest.raises(ValueError):
        store.append_listing_capture(con, {**CAPTURE, "status": "removed"}, [])
    with pytest.raises(duckdb.ConstraintException):
        con.execute("INSERT INTO listing_capture VALUES ('r','t','s','l',NULL,NULL,'removed',0)")


def test_required_fields_are_enforced():
    con = store.connect(":memory:")
    with pytest.raises(ValueError):
        store.append_listing_capture(con, {k: v for k, v in CAPTURE.items() if k != "capture_ts"}, [])
    with pytest.raises(ValueError):
        store.append_listing_capture(con, CAPTURE, [{"file_url": "x", "bates_id": "", "dataset": "1"}])


def test_parquet_roundtrip_includes_contract_tables(tmp_path):
    con = store.connect(":memory:")
    store.append_listing_capture(con, CAPTURE, FILES)
    store.export(con, str(tmp_path))
    restored = store.connect(":memory:", import_dir=str(tmp_path))
    assert restored.execute("SELECT count(*) FROM listing_capture_file").fetchone()[0] == 2


def test_export_creates_both_parquet_and_csv(tmp_path):
    con = store.connect(":memory:")
    store.append_listing_capture(con, CAPTURE, FILES)
    store.export(con, str(tmp_path))

    # Check that both Parquet and CSV files exist for each table
    for table in store.TABLES:
        parquet_file = tmp_path / f"{table}.parquet"
        csv_file = tmp_path / f"{table}.csv"
        assert parquet_file.exists(), f"{table}.parquet not created"
        assert csv_file.exists(), f"{table}.csv not created"
        assert parquet_file.stat().st_size > 0, f"{table}.parquet is empty"
        assert csv_file.stat().st_size > 0, f"{table}.csv is empty"


def test_csv_export_has_headers(tmp_path):
    con = store.connect(":memory:")
    store.append_listing_capture(con, CAPTURE, FILES)
    store.export(con, str(tmp_path))

    # Check that listing_capture_file CSV has a header row
    csv_file = tmp_path / "listing_capture_file.csv"
    lines = csv_file.read_text().splitlines()
    assert len(lines) >= 2, "CSV file should have header and data rows"

    header = lines[0]
    # Should contain the expected columns
    assert "run_id" in header
    assert "file_url" in header
    assert "bates_id" in header


def test_bronze_is_append_only_in_source():
    """D-006 / boundary B6: no UPDATE, DELETE, DROP or TRUNCATE anywhere in src."""
    pattern = re.compile(r"\b(update\s+\w+\s+set|delete\s+from|drop\s+table|truncate\s+table)\b", re.IGNORECASE)
    offenders = [
        f"{p.name}:{i}"
        for p in (Path(__file__).parent.parent / "src" / "register").glob("*.py")
        for i, line in enumerate(p.read_text().splitlines(), 1)
        if pattern.search(line)
    ]
    assert offenders == []
