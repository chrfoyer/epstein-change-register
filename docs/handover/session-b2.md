# Session B2: Source B implementation

Branch `feat/s0-wayback-impl`. Decision number D-017. Start with `/session-start b2`.

Build Slice 0 Source B from the merged spike (D-014, `SPIKE_FINDINGS.md`). Read both
first, plus `docs/handover/b-status.md`. Read-only against archive.org. Never fetch
PDFs, never use Save-Page-Now, never touch justice.gov directly (D-011).

## Order of work, one PR each

1. **Contract PR first, only if needed.** A partial capture set (some `?page=N`
   missing) must not be written as `ok`. The status enum is `ok|blocked|error|empty`
   in `src/register/contract.py`. Decide whether to add `partial` or reuse `error`,
   record it in D-017, and change the contract in its own small PR with the contract
   test updated. Session A's classifier takes completeness as an explicit input, so
   this does not block A.
2. **CDX client + interstitial detector.** Serial, 2 s between requests, honest
   User-Agent from `REGISTER_CONTACT`, backoff on 429/5xx, no parallelism. Detect the
   Akamai page by markers (`bm-verify`, `/_sec/verify`) and ~2 KB body, not by status.
3. **Listing parser** for the Drupal `<ul><li>` markup from D-014, including
   `?page=0..N` pagination and the "Last page" marker. Only court-record PDFs under
   numbered `DataSet N/` paths (mirror `FILE_URL_RE` in `src/register/analytics.py`).
4. **Persistence** through `store.append_listing_capture` only. A complete set across
   all pages in one capture window is `ok`; anything else is not `ok` and carries no
   file rows. `archive_digest` is Wayback's base32 SHA-1 and will be NULL for most rows
   (per-file CDX lookups are out of scope here); never name it sha256.
5. **Workflow job** in `.github/workflows/crawl.yml`, separate from the Source A job,
   daily, writing state to the same `data` branch Parquet.

## Fixtures

Use the fixture-builder subagent. Fixtures are synthetic reconstructions of the
markup shape and of CDX JSON, never captured HTML or real filenames.

## Deliver

Each PR on its own branch from `origin/main` (rebase first), tests green, boundary
auditor run, `docs/handover/b2-status.md`, and D-017 only for real decisions. Do not
edit `BACKLOG.md`. Report anything the classifier (session A) needs from Source B.
