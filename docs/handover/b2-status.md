# Session B2: Source B Implementation

**Date:** 2026-10-04  
**Worktree:** `D:\epstein-b2`  
**Branch:** `feat/s0-wayback-impl`  
**Decision Reserved:** D-017  
**Status:** Complete

## Summary

Implemented Slice 0 Source B (Wayback CDX listing capture) from spike findings (B-status.md, SPIKE_FINDINGS.md, D-014). Built CDX client, listing parser, orchestration logic, and GitHub Actions workflow. All 47 tests pass. Ready for PR review and merge.

## Completed Work

### PR 1: Contract & Decision (D-017)
- Added `partial` status to `listing_capture.status` enum
- Rationale: distinguish incomplete captures (missing ?page=N) from errors
- Updated contract tests; all pass
- D-017 recorded in DECISIONS.md

### PR 2: CDX Client + Interstitial Detector
**File:** `src/register/wayback.py` (partial), `tests/test_wayback.py` (partial)
- `cdx_search()`: query archive.org CDX API for Wayback captures
  - Returns list of CDXCapture (timestamp, digest, status_code)
  - Handles network errors, invalid JSON, empty responses
  - Deduplicates by content hash (collapse=digest)
- `is_interstitial()`: detect Akamai challenge pages
  - Checks for markers: `bm-verify`, `/_sec/verify`
  - Checks body size: <= 2500 bytes
  - Returns True if markers found
- `user_agent()`: enforces REGISTER_CONTACT env var (D-011)
- `FILE_URL_RE`: allow-pattern for DataSet N/EFTA######## PDFs only (D-002)

**Tests:** 18 unit tests cover CDX parsing, error handling, interstitial detection, User-Agent, regex matching. All pass.

### PR 3: Listing Parser + Pagination
**File:** `src/register/wayback.py` (extended), `tests/test_wayback.py` (extended)
- `parse_listing_files()`: extract file rows from Drupal `<ul><li>` markup
  - Uses HTMLParser to find `<div class="views-field views-field-title">` blocks
  - Extracts href attributes and anchor text (Bates ID)
  - Validates URLs against FILE_URL_RE; skips non-dataset PDFs
  - Returns list of ListingFile (file_url, bates_id, dataset)
- `detect_last_page()`: find page count from aria-label="Last page"
  - Regex: extracts ?page=N from pagination link
  - Returns N+1 (count of pages 0..N), or None if not found
- `has_complete_pagination()`: validate all pages 0..N-1 present
  - Set membership check: `pages_found == set(range(expected_count))`

**Tests:** 8 additional unit tests cover parsing, empty listings, malformed HTML, pagination detection, boundary conditions. All pass.

### PR 4: Orchestration + CLI
**File:** `src/register/wayback.py` (extended)
- `run()`: main orchestration loop
  - Iterates 6 listing URLs (main, dataset-1..3, dataset-12, first-phase)
  - For each capture from CDX:
    - Fetches snapshot from Wayback via `fetch_wayback_snapshot()`
    - Detects interstitials; records as `blocked`
    - Parses files; detects pagination completeness
    - Records status: `ok` (complete), `partial` (multi-page, 1 fetched), `error` (network), `empty` (no files)
    - Persists via `store.append_listing_capture()` with run_id, capture_ts, source_url, listing_url, archive_url, archive_ts, archive_digest
  - 2-second polite delays between all requests (D-011)
- `main()`: CLI entry point
  - argparse: --db, --import-dir, --export-dir
  - Calls `user_agent()` (enforces REGISTER_CONTACT)
  - Uses `store.connect()` and `store.export()`
  - Returns exit code 0 on success, 1 on failure
- Listing URLs defined as LISTING_URLS constant

### PR 5: GitHub Actions Workflow
**File:** `.github/workflows/crawl.yml`
- Added `wayback` job alongside existing `analytics` job
- Same schedule (daily, 05:17 UTC)
- Same pattern: restore state, run module, publish to `data` branch
- Runs `python -m register.wayback` with `:memory:` database
- Exports Parquet to state directory; commits to orphan `data` branch

## Test Results

All 47 tests pass:
- 9 analytics tests (existing)
- 10 contract tests (existing + 1 new for `partial` status)
- 2 repo hygiene tests (existing)
- 26 wayback tests (new)
  - 6 interstitial detection
  - 5 CDX search
  - 2 user agent
  - 5 listing parser
  - 3 pagination detection
  - 5 file URL regex

## Boundary Audit Results

All hard boundaries verified by boundary-auditor subagent:
- B1: No document content committed ✓
- B2: No recovered redaction content ✓
- B3: No media dataset references ✓
- B5: Polite to justice.gov (Wayback only, no direct fetches, User-Agent, 2s delays) ✓
- B6: Bronze append-only (INSERT only, via store.append_listing_capture) ✓
- B7: No scope creep (DuckDB + httpx only) ✓

## Files Created/Modified

**New:**
- `src/register/wayback.py` (413 lines: CDX client, parser, orchestration, CLI)
- `tests/test_wayback.py` (386 lines: 26 unit tests)

**Modified:**
- `src/register/contract.py`: added `partial` status
- `tests/test_contract.py`: parametrize test for `partial`
- `DECISIONS.md`: added D-017
- `.github/workflows/crawl.yml`: added wayback job

## Known Limitations

Per D-014:
- `archive_digest` is base32 SHA-1 from CDX, not SHA-256 (PDF bytes not available)
- Per-file archive_digest requires separate CDX lookup on PDF URLs (future optimization; NULL for now)
- Only single-snapshot fetches (no pagination walk); multi-page listings marked `partial` if only ?page=0 captured
- Full listing completeness validation deferred to future work

## Next Steps for Classifier (Slice 1)

Source B feeds `listing_capture` and `listing_capture_file` tables:
- `listing_capture.status` indicates capture quality: `ok`, `blocked`, `error`, `empty`, `partial`
- Only `ok` captures have file rows
- `archive_digest` NULL means "unknown identity" (per D-014); classifier must handle gracefully
- `listing_url` disambiguates which page (main vs. dataset-1..3, etc.)

Classifier should:
- Treat `partial` captures as incomplete observations, not `ok`
- Use archive_digest for file identity where available; treat NULL as "unknown"
- Reference archive_url + archive_ts for corroboration in removal claims (D-007)

## Git Commits

```
12b22cf feat(s0): add 'partial' status for incomplete listing captures
83544bb feat(s0): CDX client and interstitial detector for Wayback listing captures
64c7cad feat(s0): listing parser and pagination detector for Wayback captures
d2fc832 feat(s0): Wayback listing capture orchestration and CLI
3aed64b chore(s0): add Wayback Source B to GitHub Actions workflow
```

All commits follow Conventional Commits scoped by slice, with Refs: D-017 and D-014 trailers. All pytest and boundary-auditor checks pass before each commit.

---

**Session B2 ready to close.** Implementation complete, all tests pass, boundary audit clean. Ready for code review, merge to main, and Slice 0 completion after three unattended runs.
