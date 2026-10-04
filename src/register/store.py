"""DuckDB bronze store. Append-only (D-006): this module only ever INSERTs."""

from pathlib import Path

import duckdb

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
"""

TABLES = ("analytics_fetch", "analytics_file_observation")


def connect(db_path: str, import_dir: str | None = None) -> duckdb.DuckDBPyConnection:
    """Open the store; if `import_dir` holds Parquet state, restore it first."""
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(db_path)
    con.execute(SCHEMA)
    if import_dir:
        for table in TABLES:
            parquet = Path(import_dir) / f"{table}.parquet"
            already = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            if parquet.exists() and already == 0:
                con.execute(f"INSERT INTO {table} SELECT * FROM read_parquet(?)", [parquet.as_posix()])
    return con


def export(con: duckdb.DuckDBPyConnection, export_dir: str) -> None:
    """Write each bronze table to Parquet. Metadata only."""
    Path(export_dir).mkdir(parents=True, exist_ok=True)
    for table in TABLES:
        target = (Path(export_dir) / f"{table}.parquet").as_posix()
        con.execute(f"COPY {table} TO '{target}' (FORMAT PARQUET)")
