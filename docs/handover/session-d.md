# Session D: schema documentation and export

Branch `feat/s2-schema-export`. Decision number D-019. Start with `/session-start d`.
Slice 2 preparation. No network access.

Goal: make the bronze data reusable by someone who has never seen the code.

1. **`SCHEMA.md`** at the repo root, version `0.x` (semver, per BACKLOG Slice 2):
   every column of `analytics_fetch`, `analytics_file_observation`,
   `listing_capture`, `listing_capture_file` and the `observed_file_span` view, with
   type, nullability, meaning and an example value. Take them from
   `src/register/store.py` and `src/register/contract.py`, not from memory.
   Describe `archive_digest` as Wayback's base32 SHA-1 and never as sha256. Leave a
   clearly marked placeholder for `change_event`, which session A's PR defines.
2. **A drift test** (`tests/test_schema_docs.py`) that fails when `SCHEMA.md` and the
   real DDL disagree on a table or column name or type. Documentation that can rot
   silently is worse than none.
3. **`register export`**: write the bronze tables to Parquet and CSV in a directory.
   Metadata only; never document content. Reuse `store.export`; add CSV. Fixture tests
   with synthetic rows. Do not add a dependency.
4. **Column contract rule** in `SCHEMA.md`: what counts as a breaking change (rename,
   type change, removed column) versus compatible (new nullable column), and how the
   version bumps.

## Out of scope

Publishing to a site or releases, the change feed (needs A), and any decision about
where data is hosted. If a real decision comes up, record it in D-019.

## Deliver

PR with tests green and the boundary auditor run, `docs/handover/d-status.md`, no
edits to `BACKLOG.md`. If session A has merged `change_event`, add it; otherwise leave
the placeholder and say so.
