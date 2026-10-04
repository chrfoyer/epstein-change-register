# CLAUDE.md

Project instructions for Claude Code. Read this before doing anything in this repo.

## What this project is

An independent completeness and change register for the DOJ Epstein Library.
It records what was published, what moved, and what disappeared, with verifiable
provenance. **It does not host the documents themselves.**

Read `DECISIONS.md` before proposing architecture. Most of the obvious
suggestions have already been considered and rejected there for reasons that
still hold.

## Hard boundaries

These are not preferences. Do not propose work that crosses them.

1. **Scope is court-record and disclosure PDFs only.** Never add ingestion of
   the image or video datasets. See D-002.
2. **Never store or commit document content.** Metadata, hashes, and provenance
   only. See D-003.
3. **Never write recovered redaction content to a public table, a log, a test
   fixture, or a commit message.** Findings (page, bbox, char count) are public;
   content is restricted. See D-004.
4. **Never emit a "removed" claim on a single absence.** Two consecutive polls
   plus third-party evidence. See D-007.
5. **Be polite to justice.gov.** Conditional requests, rate limiting, honest
   User-Agent with contact details. No parallel bulk fetching.

## Working agreement

The maintainer works on this roughly one 4–6 hour block per week, often with
multi-week gaps. Optimise for picking the project back up cold.

- **Every block ends with a commit that runs.** Do not leave half-finished work
  across sessions.
- **Prefer small, complete vertical slices** over scaffolding. See `BACKLOG.md`
  for the slice breakdown and work them in order.
- **When a non-obvious decision gets made, add an entry to `DECISIONS.md`** in
  the existing format, in the same session. Record the rejected alternative.
- **Explain reasoning briefly, not exhaustively.** The maintainer is a data
  engineer — assume familiarity with SQL, ETL, dimensional modelling, and CI/CD.
  Do not explain what a primary key is.
- If a request conflicts with `DECISIONS.md`, say so and ask rather than
  silently following the newer instruction.

## Stack

- Python 3.12+, `uv` for dependency management
- DuckDB for storage; Parquet for published outputs
- `httpx` for fetching, `pymupdf` for PDF inspection
- `pytest` for tests; GitHub Actions for scheduling and CI
- Windows development machine; keep paths and shell commands portable

Do not introduce Databricks, Spark, or cloud infrastructure. That is Slice 7 and
explicitly optional — see D-005.

## Conventions

- Timestamps are UTC, stored as ISO 8601 with explicit offset.
- Hashes are SHA-256, lowercase hex.
- Table names are singular and snake_case (`observed_file`, `change_event`).
- Every table that records an observation carries `capture_ts` and `source_url`.
- Bronze is append-only. Never update or delete a bronze row. See D-006.

## Subagents

Four agents live in `.claude/agents/`. Subagents run on Haiku (see D-008).

- **boundary-auditor** — run before every commit. Read-only; reports
  violations, never fixes them.
- **doj-recon** — use to survey DOJ listing pages instead of fetching them
  directly. One instance per page, HEAD requests only for PDFs.
- **fixture-builder** — owns `tests/fixtures/`. Synthetic data only.
- **threshold-tuner** — Slice 6 only. Parallel parameter sweeps, one
  combination per instance.

## Restricted content

Restricted content (recovered redaction text, D-004) lives at
`data/restricted/**`. It is covered by a `Read` deny rule in
`.claude/settings.json`; see D-009. If the storage layout moves, move the
deny rule in the same commit.

## Testing

- Any change to the change-event classifier needs a fixture test.
- Fixtures live in `tests/fixtures/` and contain synthetic or metadata-only
  data. Never commit a real document into the repo.
- `pytest` must pass before any commit.

## Before claiming something works

Run it. Report what the output actually was, not what it should have been.
