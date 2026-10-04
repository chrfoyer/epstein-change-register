"""Source B: poll Wayback Machine for DOJ listing snapshots via CDX API (see D-011, D-014).

Records observations from archive.org CDX API of Wayback captures of DOJ listing pages.
Serial requests only; 2 seconds between CDX queries. Never fetches PDFs directly.
Detects Akamai interstitials and records them as 'blocked' captures.
"""

import argparse
import json
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import duckdb
import httpx

from register import store

# D-002: PDFs under a numbered DataSet only.
FILE_URL_RE = re.compile(
    r"^https?://(?:www\.)?justice\.gov/epstein/files/DataSet (?P<dataset>\d+)/(?P<bates>EFTA\d{8})\.pdf$"
)

# Akamai interstitial detection markers from SPIKE_FINDINGS.
INTERSTITIAL_MARKERS = (b"bm-verify", b"/_sec/verify")
INTERSTITIAL_BODY_SIZE_MAX = 2500  # ~2 KB as observed in spike


@dataclass
class CDXCapture:
    """One Wayback snapshot metadata from CDX API."""

    timestamp: str  # YYYYMMDDhhmmss
    digest: str  # base32 SHA-1 from CDX
    status_code: int


def user_agent() -> str:
    """Honest User-Agent with contact details (D-011, CLAUDE.md)."""
    contact = os.environ.get("REGISTER_CONTACT")
    if not contact:
        raise SystemExit("REGISTER_CONTACT must be set (honest User-Agent contact, see CLAUDE.md)")
    return f"epstein-change-register/0.1 (+https://github.com/chrfoyer/epstein-change-register; {contact})"


def now_utc() -> str:
    """ISO 8601 timestamp with UTC offset."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def cdx_search(
    client: httpx.Client, url: str, match_type: str = "exact"
) -> list[CDXCapture] | None:
    """Query CDX API for Wayback captures of a URL.

    Returns list of CDXCapture in reverse chronological order, or None if the query fails.
    """
    params = {
        "url": url,
        "matchType": match_type,
        "output": "json",
        "fl": "timestamp,statuscode,digest",
        "collapse": "digest",  # Deduplicate identical captures
    }

    try:
        response = client.get("https://web.archive.org/cdx/search/cdx", params=params, timeout=10)
        response.raise_for_status()
    except httpx.HTTPError:
        return None

    try:
        data = response.json()
    except json.JSONDecodeError:
        return None

    if not data or len(data) < 2:  # First row is always the header
        return None

    headers = data[0]
    try:
        ts_idx = headers.index("timestamp")
        status_idx = headers.index("statuscode")
        digest_idx = headers.index("digest")
    except ValueError:
        return None

    captures = []
    for row in data[1:]:
        if len(row) > max(ts_idx, status_idx, digest_idx):
            try:
                captures.append(
                    CDXCapture(
                        timestamp=row[ts_idx],
                        digest=row[digest_idx],
                        status_code=int(row[status_idx]),
                    )
                )
            except (ValueError, IndexError):
                continue

    return list(reversed(captures)) if captures else None


def is_interstitial(html_bytes: bytes) -> bool:
    """Detect Akamai interstitial by markers and body size (D-014 spike findings)."""
    # Check body size (~2 KB for typical Akamai challenge)
    if len(html_bytes) > INTERSTITIAL_BODY_SIZE_MAX:
        return False

    # Check for Akamai markers
    for marker in INTERSTITIAL_MARKERS:
        if marker in html_bytes:
            return True

    return False


@dataclass
class ListingFile:
    """One file row from a listing capture."""

    file_url: str
    bates_id: str
    dataset: str


def parse_listing_files(html: str, listing_url: str) -> list[ListingFile]:
    """Parse DOJ listing page HTML and extract file rows.

    Extracts court-record PDFs from Drupal `<ul><li>` markup.
    Returns empty list if parsing fails or if no files are found.
    Does not validate URLs or Bates IDs—that is done by FILE_URL_RE in persistence.
    """
    from html.parser import HTMLParser

    files = []

    class ListingParser(HTMLParser):
        """Drupal listing parser: extract file rows from <li> elements."""

        def __init__(self):
            super().__init__()
            self.in_li = False
            self.in_views_field_title = False
            self.current_file_url = None
            self.current_bates_text = None

        def handle_starttag(self, tag, attrs):
            attr_dict = dict(attrs)
            if tag == "li":
                self.in_li = True
            elif tag == "div" and attr_dict.get("class") == "views-field views-field-title":
                self.in_views_field_title = True
            elif tag == "a" and self.in_views_field_title:
                self.current_file_url = attr_dict.get("href")

        def handle_endtag(self, tag):
            if tag == "li" and self.in_li:
                # Finalize this file row
                if self.current_file_url and self.current_bates_text:
                    match = FILE_URL_RE.match(self.current_file_url)
                    if match:
                        files.append(
                            ListingFile(
                                file_url=self.current_file_url,
                                bates_id=match["bates"],
                                dataset=match["dataset"],
                            )
                        )
                self.in_li = False
                self.in_views_field_title = False
                self.current_file_url = None
                self.current_bates_text = None
            elif tag == "div" and self.in_views_field_title:
                self.in_views_field_title = False

        def handle_data(self, data):
            if self.in_views_field_title and self.current_file_url:
                # Capture the text content of the <a> tag (should be the Bates ID)
                text = data.strip()
                if text and not self.current_bates_text:
                    self.current_bates_text = text

    parser = ListingParser()
    try:
        parser.feed(html)
    except Exception:
        # If parsing fails, return empty list (will be marked as error)
        return []

    return files


def detect_last_page(html: str) -> int | None:
    """Detect the last page number from pagination aria-label.

    Returns the page count (e.g., 63 for `?page=0..62`), or None if not found.
    """
    import re

    # Look for aria-label="Last page" in pagination nav
    # The pagination shows page numbers 1-indexed, but URLs are 0-indexed
    match = re.search(r'aria-label="Last page"[^>]*href="[^"]*\?page=(\d+)"', html)
    if match:
        # Last page URL has ?page=N, and that maps to N+1 pages (0..N)
        return int(match.group(1)) + 1
    return None


def has_complete_pagination(pages_found: set[int], expected_count: int) -> bool:
    """Check if we have all pages in the expected range.

    A complete capture has all pages from 0 to expected_count-1.
    """
    return pages_found == set(range(expected_count))


# DOJ Wayback listing page URLs (from spike findings, D-014)
LISTING_URLS = [
    ("main", "https://justice.gov/epstein/doj-disclosures"),
    ("dataset-1", "https://justice.gov/epstein/doj-disclosures/data-set-1-files"),
    ("dataset-2", "https://justice.gov/epstein/doj-disclosures/data-set-2-files"),
    ("dataset-3", "https://justice.gov/epstein/doj-disclosures/data-set-3-files"),
    ("dataset-12", "https://justice.gov/epstein/doj-disclosures/data-set-12-files"),
    ("first-phase", "https://justice.gov/epstein/doj-disclosures/first-phase-production-files"),
]

POLITE_DELAY_SECONDS = 2


def fetch_wayback_snapshot(client: httpx.Client, archive_url: str) -> bytes | None:
    """Fetch a Wayback snapshot and return its HTML body, or None if it fails."""
    try:
        response = client.get(archive_url, timeout=30)
        response.raise_for_status()
        return response.content
    except httpx.HTTPError:
        return None


def run(con: duckdb.DuckDBPyConnection, client: httpx.Client) -> str:
    """Poll Wayback CDX for DOJ listing snapshots and persist observations.

    Returns 'ok' if at least one capture was successfully processed, or an error status.
    """
    run_id = uuid.uuid4().hex
    ts = now_utc()
    capture_count = 0
    error_count = 0

    for listing_name, listing_url in LISTING_URLS:
        time.sleep(POLITE_DELAY_SECONDS)
        captures = cdx_search(client, listing_url)
        if captures is None:
            error_count += 1
            continue

        # For each capture, try to fetch and parse it
        for capture in captures:
            archive_url = f"https://web.archive.org/web/{capture.timestamp}/{listing_url}"
            html_bytes = fetch_wayback_snapshot(client, archive_url)

            if html_bytes is None:
                # Network error; treat as 'error' status
                store.append_listing_capture(
                    con,
                    {
                        "run_id": run_id,
                        "capture_ts": ts,
                        "source_url": f"https://web.archive.org/cdx/search/cdx",
                        "listing_url": listing_url,
                        "archive_url": archive_url,
                        "archive_ts": capture.timestamp,
                        "status": "error",
                    },
                    [],
                )
                error_count += 1
                time.sleep(POLITE_DELAY_SECONDS)
                continue

            # Check for interstitial
            if is_interstitial(html_bytes):
                store.append_listing_capture(
                    con,
                    {
                        "run_id": run_id,
                        "capture_ts": ts,
                        "source_url": f"https://web.archive.org/cdx/search/cdx",
                        "listing_url": listing_url,
                        "archive_url": archive_url,
                        "archive_ts": capture.timestamp,
                        "status": "blocked",
                    },
                    [],
                )
                time.sleep(POLITE_DELAY_SECONDS)
                continue

            # Parse listing files
            html = html_bytes.decode("utf-8", errors="ignore")
            files = parse_listing_files(html, listing_url)

            # Detect last page for completeness check
            last_page = detect_last_page(html)

            # If we have a single page (no pagination), mark it ok
            if last_page is None and files:
                store.append_listing_capture(
                    con,
                    {
                        "run_id": run_id,
                        "capture_ts": ts,
                        "source_url": f"https://web.archive.org/cdx/search/cdx",
                        "listing_url": listing_url,
                        "archive_url": archive_url,
                        "archive_ts": capture.timestamp,
                        "status": "ok",
                        "archive_digest": capture.digest,
                    },
                    [
                        {
                            "file_url": f["file_url"],
                            "bates_id": f["bates_id"],
                            "dataset": f["dataset"],
                            "archive_digest": capture.digest,
                        }
                        for f in files
                    ],
                )
                capture_count += 1
                time.sleep(POLITE_DELAY_SECONDS)
                continue

            # If pagination exists, we need all pages for a complete capture
            # For now, mark single-page captures as ok; multi-page incomplete as partial
            # (Full pagination fetching is a future concern per D-014)
            if last_page is not None and last_page > 1:
                # Multi-page listing, but we only have one page: mark as partial
                store.append_listing_capture(
                    con,
                    {
                        "run_id": run_id,
                        "capture_ts": ts,
                        "source_url": f"https://web.archive.org/cdx/search/cdx",
                        "listing_url": listing_url,
                        "archive_url": archive_url,
                        "archive_ts": capture.timestamp,
                        "status": "partial",
                    },
                    [],
                )
            elif files:
                # Single page (no pagination), has files: mark as ok
                store.append_listing_capture(
                    con,
                    {
                        "run_id": run_id,
                        "capture_ts": ts,
                        "source_url": f"https://web.archive.org/cdx/search/cdx",
                        "listing_url": listing_url,
                        "archive_url": archive_url,
                        "archive_ts": capture.timestamp,
                        "status": "ok",
                        "archive_digest": capture.digest,
                    },
                    [
                        {
                            "file_url": f["file_url"],
                            "bates_id": f["bates_id"],
                            "dataset": f["dataset"],
                            "archive_digest": capture.digest,
                        }
                        for f in files
                    ],
                )
                capture_count += 1
            else:
                # No files found
                store.append_listing_capture(
                    con,
                    {
                        "run_id": run_id,
                        "capture_ts": ts,
                        "source_url": f"https://web.archive.org/cdx/search/cdx",
                        "listing_url": listing_url,
                        "archive_url": archive_url,
                        "archive_ts": capture.timestamp,
                        "status": "empty",
                    },
                    [],
                )

            time.sleep(POLITE_DELAY_SECONDS)

    return "ok" if capture_count > 0 else "error"


def main() -> int:
    """CLI entry point for Source B."""
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
    print(f"wayback listing capture: {status}")
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
