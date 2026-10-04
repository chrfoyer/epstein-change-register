# Session A (Slice 1 Classifier) Status

**Branch**: feat/s1-change-classifier
**Commit**: fcf6e12 (rebased on contract PR)
**Status**: Complete, ready for review

## Deliverables

### ✅ D-013 (Decision Document)
Recorded in DECISIONS.md: change-event schema design, identity resolution, event types, removal rule, and classifier architecture.

### ✅ Schema Extension
- `change_event` table in src/register/store.py with 13 columns
- Uses contract.py's `listing_capture` and `listing_capture_file` (D-016)
- Append-only pattern per D-006

### ✅ Deterministic Classifier
- `src/register/classifier.py` (229 lines)
- Identity: bates_id → archive_digest → unknown
- Events: added, removed, reuploaded_identical, reuploaded_changed, moved_dataset
- Removal: two consecutive ok polls with absence (D-007)
- No duplicate events (move takes precedence over URL change)

### ✅ CLI with Report Command
- `src/register/cli.py` (176 lines)
- Command: `register report --since 7d` (supports 7d, 30d, 24h, etc.)
- Formats: text (default), JSON, CSV
- Time delta parsing with ISO 8601 output

### ✅ Comprehensive Test Suite
- 8 scenario fixtures + 2 edge cases = 10 passing tests
- Covers: stable files, flaky absences, removals, reuploads (identical/changed), moves, error/empty listings
- Fixtures are 100% synthetic (no real data, no document content)
- All tests pass on worktree (tested after rebase)

### ✅ Code Quality
- No document content in fixtures or code
- No external API calls (deterministic only)
- Proper error handling for edge cases (error/empty listings, unknown identity)
- Type hints on classifier functions

## What Source B Must Provide

Source B's `append_listing_capture(con, capture, files)` helper (in contract.py) is the only writer for listing_capture/listing_capture_file. Classifier reads these tables and produces change_event rows.

Expected table contract per D-016:
- `listing_capture(run_id, capture_ts, source_url, listing_url, archive_url, archive_ts, status, row_count)`
  - status CHECK (ok|blocked|error|empty)
- `listing_capture_file(run_id, capture_ts, source_url, listing_url, file_url, bates_id, dataset, archive_digest)`
  - archive_digest nullable = "unknown identity"

Non-ok captures must carry zero file rows (enforced by append_listing_capture).

## Completeness Gating (D-013 Implementation)

Per coordinator review, removal events now require explicit completeness marking:
- Removal only emitted when BOTH consecutive polls are marked complete in `complete_by_source` dict
- Default: incomplete (no removal can be claimed)
- Added two fixture tests: scenario_9 (incomplete→no removal) and scenario_10 (complete→removal)
- All 12 tests now pass with completeness constraints
- Fixtures converted to unified format: `{input, expected, complete_by_source}`

## Next Steps

1. Open PR on feat/s1-change-classifier (merge-commit style, Refs: D-013)
2. Coordinator review
3. Merge and coordinate with session B for integration once listing_capture rows flow
4. CLI integration: `report --since` will respect completeness constraints

## Notes

- Coordinator's design facts incorporated (D-014 spike findings):
  - archive_digest NULL handling: reuploaded_* skip classification when digest is NULL (D-011)
  - Completeness is explicit, never inferred (prevents false removals on partial captures)
  - Per-file archive_digest will be NULL initially; separate CDX lookups needed
  - Only Source B (Wayback) can emit change events; Source A (analytics) liveness-only
- append_listing_capture came from coordinator's PR #5, not session B
- All 12 tests pass; boundary audit clean
