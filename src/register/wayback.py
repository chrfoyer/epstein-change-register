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
