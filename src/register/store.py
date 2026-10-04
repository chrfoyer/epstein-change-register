"""DuckDB bronze store. Append-only (D-006): this module only ever INSERTs."""

from pathlib import Path

import duckdb

from register import contract

SCHEMA = """
CREATE TABLE IF NOT EXISTS analytics_fetch (
    run_id VARCHAR,
    capture_ts VARCHAR,
    source_url VARCHAR,
    status VARCHAR,          -- ok | not_modified | unchanged | unexpected | error
    http_status INTEGER,
    body_sha256 VARCHAR,
    etag VARCHAR,
    last_modified VARCHAR,
    row_count INTEGER,
    excluded_count INTEGER
);
CREATE TABLE IF NOT EXISTS analytics_file_observation (
    run_id VARCHAR,
    capture_ts VARCHAR,
    source_url VARCHAR,
    file_url VARCHAR,
    bates_id VARCHAR,
    dataset VARCHAR,
    total_events INTEGER
);
CREATE OR REPLACE VIEW observed_file_span AS
SELECT file_url, bates_id, dataset,
       min(capture_ts) AS first_seen,
       max(capture_ts) AS last_seen,
       count(*) AS observation_count
FROM analytics_file_observation
GROUP BY file_url, bates_id, dataset;
CREATE TABLE IF NOT EXISTS change_event (
    capture_ts VARCHAR,
    source_url VARCHAR,
    event_type VARCHAR,
    source_name VARCHAR,
    file_url VARCHAR,
    bates_id VARCHAR,
    dataset VARCHAR,
    prior_dataset VARCHAR,
    archive_digest VARCHAR,
    prior_archive_digest VARCHAR,
    archive_url VARCHAR,
    archive_ts VARCHAR,
    notes VARCHAR
);
"""

TABLES = ("analytics_fetch", "analytics_file_observation", "listing_capture", "listing_capture_file", "change_event")

_CAPTURE_KEYS = ("run_id", "capture_ts", "source_url", "listing_url", "status")
_FILE_KEYS = ("file_url", "bates_id", "dataset")


def append_listing_capture(con: duckdb.DuckDBPyConnection, capture: dict, files: list[dict]) -> None:
    """Append one listing capture and its file rows. The only writer for these tables.

    A blocked, error or empty capture carries no file rows, so it can never read
    as a mass removal (D-007). `archive_digest` is optional; absent means unknown.
    """
    missing = [k for k in _CAPTURE_KEYS if not capture.get(k)]
    if missing:
        raise ValueError(f"listing capture missing required fields: {missing}")
    if capture["status"] not in contract.LISTING_STATUSES:
        raise ValueError(f"status must be one of {contract.LISTING_STATUSES}, got {capture['status']!r}")
    if capture["status"] != "ok" and files:
        raise ValueError(f"a {capture['status']} capture must not carry file rows")
    for f in files:
        bad = [k for k in _FILE_KEYS if not f.get(k)]
        if bad:
            raise ValueError(f"listing file missing required fields: {bad}")

    con.execute(
        "INSERT INTO listing_capture VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [capture["run_id"], capture["capture_ts"], capture["source_url"], capture["listing_url"],
         capture.get("archive_url"), capture.get("archive_ts"), capture["status"], len(files)],
    )
    if files:  # DuckDB executemany rejects an empty parameter list
        con.executemany(
            "INSERT INTO listing_capture_file VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [[capture["run_id"], capture["capture_ts"], capture["source_url"], capture["listing_url"],
              f["file_url"], f["bates_id"], f["dataset"], f.get("archive_digest")] for f in files],
        )


def connect(db_path: str, import_dir: str | None = None) -> duckdb.DuckDBPyConnection:
    """Open the store; if `import_dir` holds Parquet state, restore it first."""
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(db_path)
    con.execute(SCHEMA)
    con.execute(contract.LISTING_CAPTURE_DDL)
    con.execute(contract.LISTING_CAPTURE_FILE_DDL)
    if import_dir:
        for table in TABLES:
            parquet = Path(import_dir) / f"{table}.parquet"
            already = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            if parquet.exists() and already == 0:
                con.execute(f"INSERT INTO {table} SELECT * FROM read_parquet(?)", [parquet.as_posix()])
    return con


def export(con: duckdb.DuckDBPyConnection, export_dir: str) -> None:
    """Write each bronze table to Parquet and CSV. Metadata only."""
    Path(export_dir).mkdir(parents=True, exist_ok=True)
    for table in TABLES:
        parquet_target = (Path(export_dir) / f"{table}.parquet").as_posix()
        csv_target = (Path(export_dir) / f"{table}.csv").as_posix()
        # Escape single quotes in paths for SQL
        parquet_escaped = parquet_target.replace("'", "''")
        csv_escaped = csv_target.replace("'", "''")
        con.execute(f"COPY {table} TO '{parquet_escaped}' (FORMAT PARQUET)")
        con.execute(f"COPY {table} TO '{csv_escaped}' (FORMAT CSV, HEADER)")
