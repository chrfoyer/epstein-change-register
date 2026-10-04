# Bronze Schema — Version 0.1

This document describes the bronze tables that form the foundation of the Epstein Library change register. All tables are append-only (see D-006); columns once defined are never updated or deleted. The schema uses semantic versioning; see [Column Contract](#column-contract-and-versioning) below.

> **Metadata only.** These tables record observations, hashes, and provenance. They never contain document content or recovered redaction text (D-003, D-004).

---

## Table: `analytics_fetch`

Source A observations from analytics.usa.gov top-downloads CSV.

| Column | Type | Nullable | Meaning | Example |
|--------|------|----------|---------|---------|
| `run_id` | VARCHAR | No | Unique identifier for this fetch run | `analytics-2026-10-04-05-17` |
| `capture_ts` | VARCHAR | No | UTC timestamp of observation, ISO 8601 with offset | `2026-10-04T05:17:00+00:00` |
| `source_url` | VARCHAR | No | The URL fetched | `https://analytics.usa.gov/data/CSV/ExampleFile.csv` |
| `status` | VARCHAR | No | Result status: `ok`, `not_modified`, `unchanged`, `unexpected`, `error` | `ok` |
| `http_status` | INTEGER | Yes | HTTP status code from the request | `200` |
| `body_sha256` | VARCHAR | Yes | SHA-256 hash of the response body, lowercase hex | `3c59dc048e8850243be8079a5c74d079d5c27f7d` |
| `etag` | VARCHAR | Yes | ETag header from response, for conditional requests | `"12345-abc"` |
| `last_modified` | VARCHAR | Yes | Last-Modified header, RFC 7231 format | `Mon, 04 Oct 2026 05:17:00 GMT` |
| `row_count` | INTEGER | Yes | Number of rows parsed from the CSV | `100` |
| `excluded_count` | INTEGER | Yes | Number of rows excluded (non-court-record PDFs, per D-002) | `7` |

**Notes:**
- `status` codes: `ok` = successful fetch and parse; `not_modified` = 304, no new data; `unchanged` = 200 but hash matches prior capture; `unexpected` = received interstitial or error page; `error` = fetch failed.
- `http_status` may be absent if the request did not complete.
- `body_sha256` is present only if `status = ok`.

---

## Table: `analytics_file_observation`

Individual files observed in Source A data.

| Column | Type | Nullable | Meaning | Example |
|--------|------|----------|---------|---------|
| `run_id` | VARCHAR | No | Links to the `analytics_fetch` run that found this file | `analytics-2026-10-04-05-17` |
| `capture_ts` | VARCHAR | No | UTC timestamp of observation, ISO 8601 with offset | `2026-10-04T05:17:00+00:00` |
| `source_url` | VARCHAR | No | The source URL (analytics.usa.gov endpoint) | `https://analytics.usa.gov/data/CSV/ExampleFile.csv` |
| `file_url` | VARCHAR | No | DOJ direct link to the PDF | `https://justice.gov/epstein/files/DataSet 1/EFTA90000001.pdf` |
| `bates_id` | VARCHAR | Yes | Bates ID extracted from filename, e.g., `EFTA########` | `EFTA90000001` |
| `dataset` | VARCHAR | Yes | Dataset folder name extracted from path | `DataSet 1` |
| `total_events` | INTEGER | Yes | Page views from analytics (for context only, not part of change detection) | `2847` |

**Notes:**
- Source A cannot make removal or state-change claims (D-013); it only provides liveness evidence for the top ~100 files.
- `bates_id` and `dataset` are extracted from the URL structure and may be NULL if parsing fails.

---

## Table: `listing_capture`

Source B observations via Wayback CDX of DOJ listing pages.

| Column | Type | Nullable | Meaning | Example |
|--------|------|----------|---------|---------|
| `run_id` | VARCHAR | No | Unique identifier for this crawl run | `run_001` |
| `capture_ts` | VARCHAR | No | UTC timestamp of observation, ISO 8601 with offset | `2026-10-04T12:00:00+00:00` |
| `source_url` | VARCHAR | No | The Wayback CDX API endpoint queried | `https://archive.org/wayback/available?url=...` |
| `listing_url` | VARCHAR | No | The DOJ listing page URL being observed | `https://justice.gov/epstein/doj-disclosures/data-set-1-files` |
| `archive_url` | VARCHAR | Yes | Direct link to the Wayback snapshot | `https://web.archive.org/web/20261004120000/justice.gov/...` |
| `archive_ts` | VARCHAR | Yes | Timestamp of the Wayback capture, ISO 8601 with offset | `2026-10-04T12:00:00+00:00` |
| `status` | VARCHAR | No | Observation result: `ok`, `blocked`, `error`, `empty`, `partial` | `ok` |
| `row_count` | INTEGER | No | Number of file rows captured in this listing; 0 if `status != ok` | `50` |

**Notes:**
- `status = ok`: listing was fully parsed and row_count file entries were extracted. All expected pages (?page=0..N) were present.
- `status = blocked`: Wayback returned an Akamai interstitial or bot-check page; no files extracted.
- `status = error`: network or parsing failure; no files extracted.
- `status = empty`: listing parsed but contained no court-record PDFs under scope (D-002); row_count = 0.
- `status = partial`: listing capture was incomplete; missing one or more expected pages (?page=N) in the sequence. No file rows extracted; row_count = 0.
- `archive_url` and `archive_ts` are present only if a valid Wayback snapshot was accessed (not present for `blocked`, `error`, `partial`).
- Completeness tracking (D-013): a sequence of captures is "complete" (status="ok") if it includes all expected `?page=N` values in roughly the same time window. Captures with missing pages receive status="partial" and do not count toward completeness for removal claims.

---

## Table: `listing_capture_file`

Individual files extracted from Source B listing captures.

| Column | Type | Nullable | Meaning | Example |
|--------|------|----------|---------|---------|
| `run_id` | VARCHAR | No | Links to the `listing_capture` run | `run_001` |
| `capture_ts` | VARCHAR | No | UTC timestamp of observation, ISO 8601 with offset | `2026-10-04T12:00:00+00:00` |
| `source_url` | VARCHAR | No | The Wayback CDX API endpoint | `https://archive.org/wayback/available?url=...` |
| `listing_url` | VARCHAR | No | The DOJ listing page being observed | `https://justice.gov/epstein/doj-disclosures/data-set-1-files` |
| `file_url` | VARCHAR | No | DOJ direct link to the PDF | `https://justice.gov/epstein/files/DataSet 1/EFTA90000001.pdf` |
| `bates_id` | VARCHAR | No | Bates ID extracted from filename | `EFTA90000001` |
| `dataset` | VARCHAR | No | Dataset folder name | `DataSet 1` |
| `archive_digest` | VARCHAR | Yes | Base32 SHA-1 of the file from Wayback CDX; NULL until per-file lookup is performed (D-011) | `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` |

**Notes:**
- Every row represents one file observed in a listing capture.
- `archive_digest` is NULL initially; per-file Wayback lookups (large-scale, separate decision) will populate it.
- Never updated or deleted; a file that moves or changes identity produces a new row in a later `capture_ts`.

---

## View: `observed_file_span`

Derived view showing the temporal extent of each observed file.

| Column | Type | Meaning | Example |
|--------|------|---------|---------|
| `file_url` | VARCHAR | DOJ direct link | `https://justice.gov/epstein/files/DataSet 1/EFTA90000001.pdf` |
| `bates_id` | VARCHAR | Bates ID or NULL | `EFTA90000001` |
| `dataset` | VARCHAR | Dataset folder name | `DataSet 1` |
| `first_seen` | VARCHAR | Earliest `capture_ts` where this file was observed, ISO 8601 | `2026-10-04T12:00:00+00:00` |
| `last_seen` | VARCHAR | Latest `capture_ts` where this file was observed, ISO 8601 | `2026-10-06T12:00:00+00:00` |
| `observation_count` | BIGINT | Number of times this (file_url, bates_id, dataset) was observed | `3` |

**Notes:**
- Computed from `analytics_file_observation` (Source A) and `listing_capture_file` (Source B).
- Groups by the tuple (file_url, bates_id, dataset), which may appear in both sources.
- Used for reporting on file stability and coverage.

---

## Table: `change_event` (Placeholder)

> **Session D note:** This table is defined in Slice 1 (session A) and documented separately. It contains the change events emitted by the deterministic classifier (D-013).
> 
> When session A's PR merges, the full `change_event` schema will be documented here. For now, see `tests/fixtures/scenario_*.json` for the expected structure.

Columns (preview):
- `capture_ts`, `source_url`, `event_type`, `source_name`, `file_url`, `bates_id`, `dataset`, `prior_dataset`, `archive_digest`, `prior_archive_digest`, `archive_url`, `archive_ts`, `notes`.

---

## Column Contract and Versioning

Semantic versioning (MAJOR.MINOR.PATCH) tracks schema compatibility.

### Breaking Changes (MAJOR version bump)

These changes break backward compatibility for consumers and require a major version bump:

1. **Renamed column** — any existing column name changes.
2. **Type change** — a column's SQL type changes (e.g., VARCHAR → INTEGER), affecting deserialization.
3. **Removed column** — a column is deleted from a table (Parquet/CSV consumers relying on it will fail).

Examples:
- Rename `bates_id` → `bates_number`: breaking.
- Change `row_count` from INTEGER to VARCHAR: breaking.
- Remove the `etag` column: breaking.

### Compatible Changes (MINOR version bump)

These changes are safe for consumers and require a minor version bump:

1. **New nullable column** — a new VARCHAR, INTEGER, or other type column added at the end of the table, with all existing rows NULL.
2. **Relaxed constraint** — e.g., a column becomes nullable when it was NOT NULL before (relaxes validation).

Examples:
- Add a new nullable column `notes` to `listing_capture`: compatible.
- Change a NOT NULL column to nullable: compatible.

### Non-Events (PATCH version bump or no bump)

1. **Extended example values** in this document (e.g., showing a new Bates ID format): PATCH only.
2. **Documentation clarification** with no schema change: PATCH.
3. **New rows or data** in the same schema: no version change (it is the data, not the schema).

### Version Pinning

Consumers should pin major version at ingest:

```
COPY table FROM 'schema-0.parquet';  -- schema 0.x is compatible
COPY table FROM 'schema-1.parquet';  -- schema 1.x requires code change
```

---

## Provenance and Completeness

Every observation row carries two provenance columns:
- **`capture_ts`** — when the observation was made (UTC, ISO 8601).
- **`source_url`** — the endpoint queried (analytics.usa.gov, Wayback CDX, community mirror, etc.).

These are the "source of truth" for change detection and removal claims (D-007, D-013). Consumers can filter by source, date range, or completeness status.

---

## Restrictions

- **Never committed:** document content, recovered redaction text, personal identifiers.
- **Never exported:** restricted redaction data (stored separately under `data/restricted/`, D-004, D-009).
- **Always cited:** archive.org snapshots for removal claims (D-007), analytics observations for liveness context (D-011).
