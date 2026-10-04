# Index

Fast reference for the change register architecture. Read `CLAUDE.md` first, then use this index to jump to specific decisions or documentation.

## Decisions (DECISIONS.md)

Decisions are read-only once merged. Use Grep or Read with line ranges to fetch specific entries instead of re-reading the full file.

| ID | Title | Status | Lines | Summary |
|----|-------|--------|-------|---------|
| D-001 | Track changes prospectively | Final | 12–27 | Poll DOJ on schedule; don't reconstruct from archives |
| D-002 | Scope to court-record PDFs | Hard boundary | 30–44 | No image or video datasets; pdf-only scope |
| D-003 | Register does not host documents | Hard boundary | 48–59 | Metadata, hashes, provenance only; no mirroring |
| D-004 | Failed-redaction findings public, content restricted | Hard boundary | 62–79 | Publish geometry & page; route content to restricted schema |
| D-005 | DuckDB first, Databricks optional | Final | 82–98 | POC uses DuckDB; Databricks only if scope changes |
| D-006 | Bronze append-only, explicit history | Final | 101–112 | Model history with `capture_ts`; don't rely on Delta time-travel |
| D-007 | Removal requires two polls + proof | Hard boundary | 115–127 | No removal on first absence; cite Wayback proof |
| D-008 | Cost: opusplan, Haiku subagents | Final | 130–142 | Opus plans, Sonnet executes; Haiku subagents. No aggressive fan-out. |
| D-009 | Restricted content at `data/restricted/**` | Hard boundary | 145–158 | Enforced by Read deny rule in settings.json |
| D-010 | Trunk-based, --no-ff merges, slice tags | Final | 161–187 | One branch per slice, merge commits, D-00N trailers. GitHub protection. |
| D-011 | Observe via third-party sources only | Hard boundary | 190–228 | No direct DOJ polling; use analytics, Wayback, community. Slice 6 blocked. |
| D-012 | Jev as optional metadata-only classifier | Proposed | 232–336 | TypeSafe Jev for scope gate, anomaly triage, card text. Privacy preconditions. |
| D-013 | Change events: source-aware, deterministic, completeness-gated | Final | 339–395 | Five event types, classifier from observations. Removal source-complete only. |
| D-014 | Source B: Wayback CDX for listings | Final | 399–451 | Poll archive.org CDX; extract Bates IDs, archive_digest. No per-file digests yet. |
| D-016 | Parallel sessions: contracts in code, worktrees, handover files | Final | 455–488 | One worktree per session. Table contracts in `src/register/contract.py`. Compaction coordinated. |
| D-017 | Partial capture status for Wayback listings | Final | 491–509 | Add `partial` enum value; distinct from `error`, `ok`, `blocked`, `empty`. |
| D-018 | Code and metadata licensing | Proposed | 513–551 | Code: MIT. Metadata: CC-BY-4.0 (attribution required). |

## Documentation

| File | Purpose | Keep in context? |
|------|---------|------------------|
| `CLAUDE.md` | This project's hard boundaries and conventions | Always (5.3 KB) |
| `DECISIONS.md` | ADRs with rejected alternatives and trade-offs | By reference; use INDEX for line ranges |
| `ARCHITECTURE.md` | System design, table schema, pipeline shape | By reference; use Grep for specific sections |
| `LIMITATIONS.md` | Known gaps (Slice 6 blocked, per-file digests deferred) | By reference; link from issue comments |
| `BACKLOG.md` | Slice definitions, dependencies, "Done when" criteria | Full read when planning; readonly in branch |
| `SPIKE_FINDINGS.md` | Spike 0 research conclusions (Wayback reachability, markup) | For Slice 0 & 1 implementation; then archive |
| `README.md` | Public description, how to run, output schema | Full read once; update on release only |
| `docs/handover/*-status.md` | Per-session status; read after compaction | Keep <1 KB; move history to `docs/handover/archive/` |

## How to use this index

1. **Starting a session:** Read `CLAUDE.md` hard boundaries, then skim this INDEX.
2. **Checking a decision:** Find the decision ID above, then Read DECISIONS.md with the line range. Example: `Read(DECISIONS.md, lines=115-127)` for D-007.
3. **Looking up a term:** Use `Grep` instead of reading full files. Example: `Grep("change_event", glob="**/*.md")`.
4. **Context after compaction:** Session hook prints `preamble.md` (shared rules); then read your session's `docs/handover/<name>-status.md` for current state.

---

*Index last updated 2026-10-04. Regenerate when DECISIONS.md changes (optional script at `scripts/index_decisions.py`).*
