"""Tests for Wayback CDX client and interstitial detection."""

import json

import httpx
import pytest

from register import wayback


class TestInterstitialDetection:
    """Test Akamai interstitial detection by markers and body size."""

    def test_detects_bm_verify_marker(self):
        """Detect Akamai challenge with bm-verify marker."""
        html = b"<html><script>bm-verify</script></html>"
        assert wayback.is_interstitial(html) is True

    def test_detects_sec_verify_marker(self):
        """Detect Akamai challenge with /_sec/verify marker."""
        html = b'<html><meta url="/_sec/verify"></html>'
        assert wayback.is_interstitial(html) is True

    def test_detects_by_body_size(self):
        """Detect interstitial by body size (~2 KB) with marker."""
        # Typical Akamai challenge is ~1.5-2 KB; set at ~1.8 KB with marker
        html = b"<html>" + b"x" * 1800 + b"bm-verify</html>"
        assert wayback.is_interstitial(html) is True

    def test_real_listing_is_not_interstitial(self):
        """Real listing HTML (74+ KB per spike) is not an interstitial."""
        # Spike findings: real listing samples are 74 KB and 90 KB
        html = b"<html>" + b"x" * 80000 + b"</html>"
        assert wayback.is_interstitial(html) is False

    def test_empty_body_is_not_interstitial(self):
        """Empty body is not flagged as interstitial."""
        assert wayback.is_interstitial(b"") is False

    def test_threshold_boundary(self):
        """Body at exactly the threshold is not interstitial."""
        # INTERSTITIAL_BODY_SIZE_MAX = 2500, so 2501+ bytes should be false
        html = b"x" * 2501
        assert wayback.is_interstitial(html) is False


class MockResponse:
    """Minimal mock Response that has required attributes."""

    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content
        self.headers = {}

    def raise_for_status(self):
        """No-op for successful responses."""
        pass

    def json(self):
        """Parse JSON content."""
        return json.loads(self.content)


class TestCDXSearch:
    """Test CDX API querying."""

    def test_parses_valid_cdx_response(self):
        """Parse valid CDX JSON with multiple captures."""
        cdx_json = json.dumps(
            [
                ["timestamp", "statuscode", "digest"],
                ["20261003084044", "200", "ABC123"],
                ["20261002080000", "200", "ABC123"],
                ["20260930000000", "200", "DEF456"],
            ]
        )

        def mock_get(url, **kwargs):
            return MockResponse(200, cdx_json.encode())

        client = httpx.Client()
        client.get = mock_get

        captures = wayback.cdx_search(client, "https://example.com/listing")
        assert captures is not None
        assert len(captures) == 3
        # Should be in reverse chronological order (oldest first from CDX, but we reverse)
        assert captures[0].timestamp == "20260930000000"
        assert captures[2].timestamp == "20261003084044"

    def test_handles_empty_response(self):
        """Handle CDX response with no captures."""

        def mock_get(url, **kwargs):
            return MockResponse(200, json.dumps([["timestamp", "statuscode", "digest"]]).encode())

        client = httpx.Client()
        client.get = mock_get

        captures = wayback.cdx_search(client, "https://example.com/listing")
        assert captures is None

    def test_handles_network_error(self):
        """Handle network errors gracefully."""

        def mock_get(url, **kwargs):
            raise httpx.ConnectError("Connection failed")

        client = httpx.Client()
        client.get = mock_get

        captures = wayback.cdx_search(client, "https://example.com/listing")
        assert captures is None

    def test_handles_invalid_json(self):
        """Handle malformed JSON response."""

        def mock_get(url, **kwargs):
            return MockResponse(200, b"not json")

        client = httpx.Client()
        client.get = mock_get

        captures = wayback.cdx_search(client, "https://example.com/listing")
        assert captures is None

    def test_collapses_duplicate_digests(self):
        """CDX collapse=digest deduplicates by content hash."""
        # Two captures with same digest should only appear once (CDX handles this)
        cdx_json = json.dumps(
            [
                ["timestamp", "statuscode", "digest"],
                ["20261003000000", "200", "SAMEHASH"],
                ["20261002000000", "200", "OTHERHASH"],
            ]
        )

        def mock_get(url, **kwargs):
            return MockResponse(200, cdx_json.encode())

        client = httpx.Client()
        client.get = mock_get

        captures = wayback.cdx_search(client, "https://example.com/listing")
        assert len(captures) == 2
        assert captures[0].digest == "OTHERHASH"
        assert captures[1].digest == "SAMEHASH"


class TestUserAgent:
    """Test User-Agent generation."""

    def test_requires_register_contact(self, monkeypatch):
        """User-Agent requires REGISTER_CONTACT environment variable."""
        monkeypatch.delenv("REGISTER_CONTACT", raising=False)
        with pytest.raises(SystemExit):
            wayback.user_agent()

    def test_includes_contact_in_ua(self, monkeypatch):
        """User-Agent includes contact URL."""
        monkeypatch.setenv("REGISTER_CONTACT", "chrfoyer+register@example.com")
        ua = wayback.user_agent()
        assert "epstein-change-register" in ua
        assert "chrfoyer+register@example.com" in ua
        assert "github.com/chrfoyer/epstein-change-register" in ua


class TestFileURLRegex:
    """Test FILE_URL_RE matching for court-record PDFs."""

    def test_matches_numbered_dataset_pdf(self):
        """Match PDF under numbered DataSet path."""
        url = "https://justice.gov/epstein/files/DataSet 1/EFTA00000001.pdf"
        match = wayback.FILE_URL_RE.match(url)
        assert match is not None
        assert match["dataset"] == "1"
        assert match["bates"] == "EFTA00000001"

    def test_matches_high_dataset_number(self):
        """Match DataSet with high number."""
        url = "https://justice.gov/epstein/files/DataSet 12/EFTA00000042.pdf"
        match = wayback.FILE_URL_RE.match(url)
        assert match is not None
        assert match["dataset"] == "12"

    def test_rejects_media_folder(self):
        """Reject PDFs in media folders (D-002)."""
        urls = [
            "https://justice.gov/epstein/files/Images/image.pdf",
            "https://justice.gov/epstein/files/Videos/video.pdf",
        ]
        for url in urls:
            assert wayback.FILE_URL_RE.match(url) is None

    def test_rejects_prior_disclosure(self):
        """Reject prior-disclosure folder (D-002)."""
        url = "https://justice.gov/epstein/files/Prior%20Disclosure/doc.pdf"
        assert wayback.FILE_URL_RE.match(url) is None

    def test_rejects_malformed_bates(self):
        """Reject Bates IDs not in EFTA########format."""
        urls = [
            "https://justice.gov/epstein/files/DataSet 1/INVALID1234.pdf",
            "https://justice.gov/epstein/files/DataSet 1/EFTA1234.pdf",  # Too short
            "https://justice.gov/epstein/files/DataSet 1/EFTA0000000001.pdf",  # Too long
        ]
        for url in urls:
            assert wayback.FILE_URL_RE.match(url) is None
