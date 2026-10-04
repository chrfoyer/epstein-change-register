# Architecture: Epstein Library Change Register

This document describes the data pipeline, design decisions, and current status of the change register project. If you're new to the project, read `CLAUDE.md` and `README.md` first, then return here.

## Core principle

The register observes what was published, what moved, and what disappeared—with verifiable provenance. **It does not host or download documents themselves.** All observations come from third-party sources (analytics feeds, Wayback captures, community submissions), never from justice.gov directly.

## Data flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA SOURCES                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ Source A: analytics.usa.gov CSV       [BUILT] Runs daily                │
│   - Top 100 downloads from DOJ site   - Serial requests, conditional    │
│   - File URLs, Bates IDs, counts      - Live data only (no removals)    │
│                                                                          │
│ Source B: Wayback CDX API             [PLANNED] D-014 ready             │
│   - Historical listing page captures  - Listing URLs → archive captures │
│   - File metadata from Drupal markup  - archive_digest fingerprints     │
│   - Pagination: pages 0..62           - Completeness-gated status       │
│                                                                          │
│ Source C: Community hash lists        [PLANNED] D-011 consequence       │
│   - Claimed hashes with attribution   - Third-party verification        │
│   - E.g. yung-megafone/Epstein-Files                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      BRONZE TABLES (Append-only)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ analytics_fetch                  listing_capture                        │
│   run_id, capture_ts               run_id, capture_ts                   │
│   source_url, status               source_url, listing_url              │
│   http_status, body_sha256         archive_url, archive_ts              │
│   etag, last_modified              status (ok|blocked|error|empty)      │
│   row_count, excluded_count        row_count                            │
│                                                                          │
│ analytics_file_observation      listing_capture_file                    │
│   run_id, capture_ts               run_id, capture_ts                   │
│   file_url, bates_id, dataset      file_url, bates_id, dataset          │
│   total_events                     archive_digest (nullable)            │
│                                                                          │
│ View: observed_file_span                                                │
│   Aggregates: first_seen, last_seen, observation_count per file         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLASSIFIER (Slice 1) [PLANNED]                       │
├─────────────────────────────────────────────────────────────────────────┤
│ Input: Bronze tables (observations)                                      │
│ Rules:                                                                   │
│   - Document identity: Bates number → Wayback archive_digest (D-011)    │
│   - Removal: 2 consecutive absences + archive proof (D-007)              │
│   - Reuploaded: same Bates, different archive_digest (D-013)            │
│   - Moved: URL changed, Bates stays same (D-013)                        │
│ Output: change_event table                                              │
│   Event types: added, removed, reuploaded_identical,                    │
│                reuploaded_changed, moved_dataset, unknown               │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                 PUBLISHED OUTPUTS (Slice 2) [PLANNED]                   │
├─────────────────────────────────────────────────────────────────────────┤
│ change_event.parquet        Daily snapshot of all events                │
│ change_event.csv            Queryable format                            │
│ change_feed.json            Weekly reverse-chronological                │
│ SCHEMA.md                   Documented column contract (semver)         │
│                                                                          │
│ Slice 3 Artifacts:                                                       │
│   - Chart: cumulative live vs. removed over time                        │
│   - Chart: mean redaction coverage per release date                     │
│   - Weekly card feed with links to DOJ + archive snapshots              │
└─────────────────────────────────────────────────────────────────────────┘
```

## The three hard constraints that shape everything

These are not preferences. See [DECISIONS.md](../DECISIONS.md) for full rationale.

1. **Never store document content** ([D-003](../DECISIONS.md#d-003--the-register-does-not-host-documents))  
   Metadata, hashes, and provenance only. This sidesteps storage cost, bandwidth, takedown risk, and inadvertent republication of unredacted victim identities.

2. **Never download from justice.gov** ([D-011](../DECISIONS.md#d-011--observe-via-third-party-sources-never-download-from-justicegov))  
   PDFs sit behind an age gate; listings behind Akamai bot checks. Passing either defeats access controls DOJ put in place. Use only third-party observations: analytics feeds, Wayback captures, community lists. Consequence: PDF bytes are unavailable, so [Slice 6 (redaction detection) is blocked](../LIMITATIONS.md) until a lawful byte source appears.

3. **Never emit "removed" on a single absence** ([D-007](../DECISIONS.md#d-007--removed-requires-two-consecutive-absences-and-third-party-evidence))  
   Require two consecutive polls plus archive proof. Flaky listings, rate limits, and re-uploads all look like removal on one poll. Publishing "DOJ deleted this" on that evidence would discredit the register.

## Critical decisions and their consequences

**Why identity can be unknown** ([D-011 consequence](../DECISIONS.md#d-011--observe-via-third-party-sources-never-download-from-justicegov))  
Bates numbers are stable; they're in the PDF filename. But without downloading the PDF, we can't verify one beyond the filename. If a file moves to a new URL, we check Wayback's `archive_digest` (base32 SHA-1 from CDX). If both are missing, the file is "unknown identity," and a second observation of a similar-sounding file cannot be marked "changed"—it's a separate unknown. This is conservative but defensible.

**Why Source A cannot emit removals** ([D-013](../DECISIONS.md#d-013--removed-requires-two-poll-completeness-gating-d-007-consequence))  
Analytics.usa.gov shows *only* top downloads—a liveness signal, not completeness. A file dropping out of the top 100 means it was downloaded less, not that it was deleted. Removals can only come from Source B (Wayback) and Source C (community lists), where we have historical snapshots to compare.

**Why Slice 6 is blocked** ([D-011 + D-004](../DECISIONS.md#d-011--observe-via-third-party-sources-never-download-from-justicegov))  
Redaction detection needs PDF bytes: compare the embedded text layer against OCR of a rendered page. Without a lawful byte source (DOJ allowlist, API feed, or verified Wayback PDF captures), this slice cannot start. It would require defeating the age gate or relying on untrusted archives. If no byte source appears, the feature becomes a `LIMITATIONS.md` write-up instead.

**Why two-poll completeness gating matters** ([D-007, D-013](../DECISIONS.md#d-007--removed-requires-two-consecutive-absences-and-third-party-evidence))  
A single poll that looks empty could be a network glitch, a bot-check interstitial, or a re-upload under a new filename. Recording it as a mass removal would poison the change feed. Instead, mark status as `blocked` or `error`, and require a second identical absence before firing a removal event. This delays removal signals but keeps them credible.

## Slice status

**Slice 0 — Start the clock**  
*Ships:* a crawler that has been running since day one.  
- Source A (analytics.usa.gov): **Built.** Running daily since 2026-10-04; first live run collected 93 PDFs with 7 excluded. State synced to Parquet on `data` branch. Uses conditional requests (`If-None-Match`), polite delay, and an identifiable User-Agent.
- Source B (Wayback CDX): **Planned.** D-014 decided 2026-10-04; spike confirmed archive.org is reachable, 6 listing pages with 5–134 captures each contain real DOJ markup. Implementation awaits Slice 0 completion. Will parse Drupal listing markup, handle pagination, and record status as `ok` only for complete page sets.
- Source C (community hashes): **Planned.** Yung-megafone/Epstein-Files as initial source, to be integrated as claimed hashes with attribution.
- Done when: three consecutive unattended runs complete successfully (0 of 3 so far).

**Slice 1 — First real output**  
*Ships:* a text report of what changed, generated from real observations.  
- `change_event` table with event types: `added`, `removed`, `reuploaded_identical`, `reuploaded_changed`, `moved_dataset`, `unknown`.
- Removal rule: present in at least two consecutive polls + archive proof. Identity resolved via Bates or `archive_digest`; NULL means unknown.
- CLI: `report --since 7d` prints week's events.
- Unit tests with fixture data.
- Status: **Not started.** Blocked on Source B implementation and Slice 0 completion.

**Slice 2 — Make it reusable**  
*Ships:* a public dataset others can build on.  
- Parquet + CSV daily exports of gold tables.
- `SCHEMA.md` with documented, semver'd column contract.
- Test fixtures with expected values asserted in CI.
- `LIMITATIONS.md` explaining what this cannot tell you (D-003 prevents document hosting; D-011 prevents redaction detection; D-007 delays removal signals).
- Status: **Planned.** Depends on Slice 1 completion.

**Slice 3 — The shareable artifact**  
*Ships:* a public page for portfolios.  
- Chart: cumulative documents live vs. removed over time.
- Chart: mean redaction coverage per release date (placeholder until Slice 6, if it ships).
- Weekly card feed, reverse-chronological, plain language.
- Every card links to DOJ URL + archive snapshot.
- Static site build, under 2s load time.
- Status: **Planned.** Depends on Slice 2.

**Slices 4–5**  
*Slice 4:* Provenance hardening (Wayback per-file CDX, Save-Page-Now requests, corroboration counts).  
*Slice 5:* Employer-facing (final README, decision log, CI badge, cost doc).  
Status: **Planned** for after Slice 3.

**Slice 6 — Redaction coverage**  
*Ships:* the "did this get more redacted" feature.  
Status: **Blocked on lawful byte source.** Do not start until DOJ allowlists PDFs, provides an API, or verified Wayback PDF captures become available. If none appears by Slice 5 completion, document why in `LIMITATIONS.md` and move on.

**Slice 7 — Databricks port**  
*Ships:* the same pipeline on managed infrastructure (optional for cost/resume comparison).  
Status: **Planned but optional.** Only if the maintainer chooses; the product does not need it.

## Open questions that will change the architecture

1. **D-012: Which LLM provider for the advisory classifier?**  
   TypeSafe Jev (direct) or OpenRouter alpha? Decision affects how much metadata-only inference is available for scope gating and anomaly triage in Slice 3. Not before Slice 1; blocked on reading privacy terms and confirming data retention settings.

2. **D-017: Can Source B pagination completeness be tracked reliably?**  
   Spike found pagination markers (`?page=0`..`?page=62`) in Wayback captures. But can we reliably detect when a page set is *complete* vs. *partial*? If not, removal signals become impossible (we can't distinguish a truncated listing from a real removal). This is the critical risk in Source B implementation.

3. **Slice 6 unblock: Does a lawful byte source appear?**  
   - DOJ allowlist or API feed?
   - Verified Wayback PDF captures (archive.org never served bulk ZIPs)?
   - Community mirror with its own decision (raises D-002 and D-003 questions)?  
   If yes: Slice 6 starts. If no by Slice 5 end: document as limitation and ship without it.

## How decisions are tracked

Every commit that touches a decision includes a `Refs: D-0NN` trailer (Conventional Commits). See [DECISIONS.md](../DECISIONS.md) for the full decision log, rationale, and what would change each answer.

For background on the slice system, see [BACKLOG.md](../BACKLOG.md). For parallel-session rules, see [D-016](../DECISIONS.md#d-016--parallel-sessions-contracts-in-code-one-worktree-each-handover-files).
