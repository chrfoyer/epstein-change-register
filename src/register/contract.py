"""Shared bronze table contract between sources and the classifier.

Source B (Wayback listing captures) writes these tables; the Slice 1 classifier
reads them. Both go through `store.append_listing_capture` and the DDL here, so a
mismatch fails `tests/test_contract.py` instead of surfacing at review.
Append-only (D-006). Every table carries `capture_ts` (UTC ISO 8601 with offset)
and `source_url`.
"""

LISTING_STATUSES = ("ok", "blocked", "error", "empty")

_STATUS_LIST = ", ".join(f"'{s}'" for s in LISTING_STATUSES)

LISTING_CAPTURE_DDL = f"""
CREATE TABLE IF NOT EXISTS listing_capture (
    run_id VARCHAR,
    capture_ts VARCHAR,
    source_url VARCHAR,
    listing_url VARCHAR,
    archive_url VARCHAR,
    archive_ts VARCHAR,
    status VARCHAR CHECK (status IN ({_STATUS_LIST})),
    row_count INTEGER
);
"""

LISTING_CAPTURE_FILE_DDL = """
CREATE TABLE IF NOT EXISTS listing_capture_file (
    run_id VARCHAR,
    capture_ts VARCHAR,
    source_url VARCHAR,
    listing_url VARCHAR,
    file_url VARCHAR,
    bates_id VARCHAR,
    dataset VARCHAR,
    archive_digest VARCHAR      -- nullable: missing means unknown, never changed (D-011)
);
"""

# Expected columns, in order, for the contract test.
LISTING_CAPTURE_COLUMNS = (
    ("run_id", "VARCHAR"),
    ("capture_ts", "VARCHAR"),
    ("source_url", "VARCHAR"),
    ("listing_url", "VARCHAR"),
    ("archive_url", "VARCHAR"),
    ("archive_ts", "VARCHAR"),
    ("status", "VARCHAR"),
    ("row_count", "INTEGER"),
)
LISTING_CAPTURE_FILE_COLUMNS = (
    ("run_id", "VARCHAR"),
    ("capture_ts", "VARCHAR"),
    ("source_url", "VARCHAR"),
    ("listing_url", "VARCHAR"),
    ("file_url", "VARCHAR"),
    ("bates_id", "VARCHAR"),
    ("dataset", "VARCHAR"),
    ("archive_digest", "VARCHAR"),
)
