"""Source B: poll Wayback Machine for DOJ listing snapshots via CDX API (see D-011, D-014).

Records observations from archive.org CDX API of Wayback captures of DOJ listing pages.
Serial requests only; 2 seconds between CDX queries. Never fetches PDFs directly.
Detects Akamai interstitials and records them as 'blocked' captures.
"""

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx

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
