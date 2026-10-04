# Spike 0 Source B: Wayback CDX Observation — Findings

**Date:** 2026-10-04  
**Session:** B (Wayback source, feat/s0-wayback-source)  
**Status:** Complete

## Step 0: Archive.org Reachability

**Finding:** ✓ archive.org CDX is reachable

- Tested: `https://web.archive.org/cdx/search/cdx`
- Result: HTTP 200 with valid JSON response on first attempt
- No Akamai interstitials or service unavailability
- Implication: **Unblock Source B** — proceed with full implementation

**Note:** archive.org was reported "Temporarily Offline" on 2026-10-04, but recovered before spike execution.

## Step 1: CDX Capture Inventory

**Finding:** Rich capture history across all DOJ listing pages

All six queried pages have captures:

| Page | Captures | Date Range | Status |
|------|----------|-----------|--------|
| Main (`doj-disclosures`) | 134 | Dec 2025 – Oct 2026 | ✓ OK |
| Dataset-1 | 25 | Dec 2025 – Apr 2026 | ✓ OK |
| Dataset-2 | 16 | Dec 2025 – Mar 2026 | ✓ OK |
| Dataset-3 | 11 | Dec 2025 – Mar 2026 | ✓ OK |
| Dataset-12 | 19 | Jan – May 2026 | ✓ OK |
| First-phase | 5 | Feb – Apr 2026 | ✓ OK |

No 403 (blocked) or 429 (rate limit) responses in any CDX query.

**Implications:**
- Wayback has captured most listing page updates for ~10 months
- Multiple snapshots per page enable change detection
- No indication of bot-wall responses in captures (unlike live justice.gov)

## Step 2: Real Listing Captures (Samples)

**Finding:** Wayback snapshots contain real listing HTML, not interstitials

Two sample captures examined:

**Capture 1: Main listing (2026-10-03)**
- URL: `justice.gov/epstein/doj-disclosures`
- Wayback: `https://web.archive.org/web/20261003084044id_/justice.gov/epstein/doj-disclosures`
- Status: 200 OK
- Content: 90,577 bytes of real HTML
- Structure: Has 140 links, pagination controls, Bates ID patterns visible
- **Result:** ✓ Real listing, not interstitial

**Capture 2: Dataset-1 listing (2026-04-24)**
- URL: `justice.gov/epstein/doj-disclosures/data-set-1-files`
- Wayback: `https://web.archive.org/web/20260424000543id_/justice.gov/epstein/doj-disclosures/data-set-1-files`
- Status: 200 OK
- Content: 74,242 bytes of real HTML
- Structure: Has 126 navigation links, 100 PDF links, pagination controls, Bates ID patterns
- **Result:** ✓ Real listing, not interstitial

**Implication:** We can parse these listings to extract file metadata, URLs, and Bates IDs.

## Step 3: Markup Structure (doj-recon Complete)

**Main Listing Page (Landing/Navigation)**
- Structure: Drupal 10 CMS with accordion navigation
- Links to dataset pages use `data-entity-uuid` attributes (stable Drupal node identifiers)
- Example: `data-entity-uuid="899d45d5-2dd1-46e2-8d4e-6bf8f0aeacd2"` for Data Set 1
- Selector: `div.usa-accordion__content a[data-entity-type="node"]`
- No pagination (links point directly to dataset pages)

**Dataset Listing Pages (File Lists)**
- Structure: Drupal 10 CMS-rendered `<ul><li>` list
- Row markup: Each file is a `<li>` with nested `<div class="views-field views-field-title">`
- File URL: In `<a href="...">` attribute (absolute URLs to justice.gov PDFs)
- Display name: Text content of `<a>` tag (Bates ID + `.pdf`, e.g., `EFTA00000001.pdf`)
- Row selector: `div.views-field.views-field-title` or `ul li`
- Bates ID location: Extracted from filename (EFTA + 8-digit zero-padded number)
- Bates ID format: EFTA00000001, EFTA00000002, etc. (stable across re-uploads if naming preserved)

**Pagination**
- Type: Query parameter, 0-indexed
- Parameter: `?page=0` through `?page=62` (63 pages total in sample)
- Display: Shows as "Page 1" for `?page=0`, "Page 2" for `?page=1`, etc.
- Navigation markup: `<nav aria-label="Pagination" class="usa-pagination">`
- Completion detection: Last page link has `aria-label="Last page"`
- Previous/Next: Class `usa-pagination__next-page`

**Metadata in Markup**
- File size: **Absent** — not in markup
- Modification date: **Absent** — not in markup
- Hash/checksum: **Absent** — not in markup
- **Implication:** Use archive_digest from CDX for fingerprinting; never rely on mtime

## Assessment: Can We Build Source B?

### Go Criteria — All Met ✓

1. **Archive.org reachable?** ✓ YES
2. **Captures exist?** ✓ YES (rich history)
3. **Captures are real listings?** ✓ YES (not interstitials)
4. **Can we parse them?** ✓ LIKELY (markup analysis pending, but structure present)
5. **Do captures have files?** ✓ YES (100+ files in one sample, link patterns present)

### Implementation Readiness

**Go decision: YES**

- Build a read-only CDX client to enumerate listing captures
- Implement interstitial detection (status "blocked" if bot-check detected)
- Write listing parser for DOJ's markup (structure pending doj-recon)
- Extract file metadata (URLs, Bates IDs, CDX digests)
- Write to `listing_capture` and `listing_capture_file` tables (from shared contract)
- Schedule as daily GitHub Actions job alongside Source A

**Scope:**
- Only court-record PDFs under numbered `DataSet N/` paths (D-002 compliance)
- Exclude media and prior-disclosure folders (allow-pattern, mirror FILE_URL_RE from analytics.py)
- Never fetch PDFs themselves (D-011 compliance)
- Record archive_url and archive_ts per file

**Risks & Mitigations:**
- Wayback capture completeness: listings may be newer than available captures
  - Mitigation: Record both "ok" (complete listing) and "empty" (no captures) status
- Markup changes: DOJ may change listing HTML structure
  - Mitigation: Robust parsing with data-attribute fallbacks; test fixtures with multiple versions
- Rate limiting: Wayback may throttle many serial requests
  - Mitigation: Polite delays between requests, conditional requests if supported

## Next: Detailed Implementation Plan

Once doj-recon completes, finalize D-014 with:
- Exact markup patterns observed
- Parser algorithm (row extraction, pagination handling)
- Error handling strategy (interstitial detection, malformed rows)
- Test fixture strategy (capture snapshots + expected outputs)

Then build:
1. `src/register/cdx_client.py` — CDX query client
2. `src/register/wayback_listing_parser.py` — HTML parser for DOJ listings
3. `tests/test_wayback_*` — Parser fixtures and tests
4. `.github/workflows/crawl.yml` — Add "Source B" job (keep Source A job untouched)
5. Update `BACKLOG.md` Source B status from "blocked" to "done" once all three unattended runs complete

**Estimated effort:** 2–3 working sessions (6–9 hours total)

---

## References

- **D-011:** Why we observe via third-party sources, never directly from justice.gov
- **D-013:** Change event classification rules and source-aware claims
- **BACKLOG.md Slice 0:** Source B requirements
- **CLAUDE.md § Hard boundaries:** Scope (court-record PDFs only), no content storage, polite requests
