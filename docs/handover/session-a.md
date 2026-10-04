# Session A: Slice 1 change-event classifier

Branch `feat/s1-change-classifier`. Decision number D-013.

Implement Slice 1 from `BACKLOG.md`: the `change_event` table, a deterministic
classifier, and a `report --since 7d` CLI, driven only by synthetic fixtures. No
network access.

## Settle first, and record in D-013

1. **Source completeness.** `analytics_file_observation` (Source A) is only the
   ~100 most-downloaded files. It supports "seen live on date X" and nothing else:
   no added, no removed, no moved. Only `listing_capture` and
   `listing_capture_file` rows from a complete listing can produce events. Give the
   classifier an explicit notion of which sources are complete, and make the report
   say plainly what it can and cannot claim. Add a liveness-only section for
   Source A data.
2. **Identity** is `bates_id` (`EFTA########`). Without one it is `archive_digest`.
   A missing digest means "unknown", never "changed" (D-011).
3. **Event types:** added, removed, reuploaded_identical, reuploaded_changed,
   moved_dataset. D-007: removed needs absence from two consecutive `ok` listings
   and an archive capture proving the file was previously live. A `blocked`,
   `error` or `empty` listing emits nothing, never a mass removal.

## Fixtures

Use the fixture-builder subagent; it owns `tests/fixtures/`. Cover every scenario
in its definition, especially the error and empty listing cases. Synthetic ids
only (`EFTA9xxxxxxx`). Any classifier change needs a fixture test.

## Deliver

Schema, classifier, CLI, tests, D-013, `docs/handover/a-status.md`, and a short
note of anything Source B must provide that `src/register/contract.py` does not.
The listing tables come from the contract; do not redefine them.
