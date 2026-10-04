"""Source A: poll analytics.usa.gov's DOJ top-downloads CSV (see D-011).

Records which court-record PDFs DOJ's own analytics saw downloaded. Liveness
evidence only: no document bytes are fetched, no hashes of documents exist here.
One serial request per run.
"""

import argparse
import csv
import hashlib
import io
import os
import re
import sys
import uuid
from datetime import datetime, timezone

import duckdb
import httpx

from register import store

SOURCE_URL = "https://analytics.usa.gov/data/justice/top-downloads-yesterday.csv"
EXPECTED_HEADER = ["linkUrl", "page_title", "page", "total_events"]

# D-002: PDFs under a numbered DataSet only. Media, prior-disclosure folders and
# anything else is excluded by construction, not by blocklist.
FILE_URL_RE = re.compile(
    r"^https?://(?:www\.)?justice\.gov/epstein/files/DataSet (?P<dataset>\d+)/(?P<bates>EFTA\d{8})\.pdf$"
)


def user_agent() -> str:
    contact = os.environ.get("REGISTER_CONTACT")
    if not contact:
        raise SystemExit("REGISTER_CONTACT must be set (honest User-Agent contact, see CLAUDE.md)")
    return f"epstein-change-register/0.1 (+https://github.com/chrfoyer/epstein-change-register; {contact})"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse(text: str) -> tuple[list[dict], int] | None:
    """Return (kept rows, excluded count), or None if the body is not the expected CSV."""
    reader = csv.reader(io.StringIO(text))
    if next(reader, None) != EXPECTED_HEADER:
        return None
    kept, excluded = [], 0
    for row in reader:
        if len(row) != 4:
            excluded += 1
            continue
        match = FILE_URL_RE.match(row[0])
        if not match:
            excluded += 1
            continue
        kept.append(
            {
                "file_url": row[0],
                "bates_id": match["bates"],
                "dataset": match["dataset"],
                "total_events": int(row[3]),
            }
        )
    return kept, excluded


def _last_fetch(con: duckdb.DuckDBPyConnection) -> tuple[str | None, str | None]:
    row = con.execute(
        "SELECT etag, body_sha256 FROM analytics_fetch "
        "WHERE status IN ('ok', 'unchanged') ORDER BY capture_ts DESC LIMIT 1"
    ).fetchone()
    return row if row else (None, None)


def _log_fetch(con, run_id, ts, status, http_status=None, sha=None, response=None, rows=None, excluded=None):
    headers = response.headers if response is not None else {}
    con.execute(
        "INSERT INTO analytics_fetch VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [run_id, ts, SOURCE_URL, status, http_status, sha, headers.get("etag"),
         headers.get("last-modified"), rows, excluded],
    )


def run(con: duckdb.DuckDBPyConnection, client: httpx.Client) -> str:
    run_id = uuid.uuid4().hex
    ts = now_utc()
    last_etag, last_sha = _last_fetch(con)
    request_headers = {"If-None-Match": last_etag} if last_etag else {}

    try:
        response = client.get(SOURCE_URL, headers=request_headers)
    except httpx.HTTPError:
        _log_fetch(con, run_id, ts, "error")
        return "error"

    if response.status_code == 304:
        _log_fetch(con, run_id, ts, "not_modified", 304, response=response)
        return "not_modified"

    sha = hashlib.sha256(response.content).hexdigest()
    parsed = parse(response.text) if response.status_code == 200 else None
    if parsed is None:
        # Bot wall, error page, or format change. Never an empty listing (D-007).
        _log_fetch(con, run_id, ts, "unexpected", response.status_code, sha, response)
        return "unexpected"

    rows, excluded = parsed
    if sha == last_sha:
        _log_fetch(con, run_id, ts, "unchanged", 200, sha, response, len(rows), excluded)
        return "unchanged"

    _log_fetch(con, run_id, ts, "ok", 200, sha, response, len(rows), excluded)
    con.executemany(
        "INSERT INTO analytics_file_observation VALUES (?, ?, ?, ?, ?, ?, ?)",
        [[run_id, ts, SOURCE_URL, r["file_url"], r["bates_id"], r["dataset"], r["total_events"]] for r in rows],
    )
    return "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="data/register.duckdb")
    parser.add_argument("--import-dir", help="restore bronze state from Parquet before running")
    parser.add_argument("--export-dir", help="write bronze state to Parquet after running")
    args = parser.parse_args()

    con = store.connect(args.db, args.import_dir)
    with httpx.Client(headers={"User-Agent": user_agent()}, timeout=30, follow_redirects=False) as client:
        status = run(con, client)
    if args.export_dir:
        store.export(con, args.export_dir)
    print(f"analytics fetch: {status}")
    return 0 if status in ("ok", "unchanged", "not_modified") else 1


if __name__ == "__main__":
    sys.exit(main())
