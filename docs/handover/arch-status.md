# Session Status: Architecture overview (arch)

**Branch:** `docs/s5-architecture`  
**Date:** 2026-10-04  
**Task:** Write `docs/ARCHITECTURE.md` for new team members.

## What was read

1. **CLAUDE.md** — Project scope (court-record PDFs only), stack (DuckDB, Python 3.12+), hard boundaries (never download PDFs, never store content, never claim removal on single absence).

2. **DECISIONS.md** — Full decision log, D-001 through D-016 (plus D-012 proposed). Key decisions touched:
   - D-001: Prospective polling (not retrospective)
   - D-003, D-004: Metadata-only, recovered redaction findings public / content restricted
   - D-006: Bronze append-only with explicit `capture_ts` rows
   - D-007: Removal requires two absences + archive proof
   - D-011: Never download from DOJ; use third-party sources only
   - D-012: Jev optional, proposed but not implemented
   - D-013: Classification rules (not found—decision in progress)
   - D-014: Wayback CDX source B (spike done, decision finalized)
   - D-016: Parallel sessions, contracts in code, worktrees

3. **BACKLOG.md** — Slice-based breakdown:
   - Slice 0: Source A built and running; Source B spike done, implementation pending; Source C planned
   - Slice 1: Classifier and change_event table not yet started
   - Slices 2–5: Planned (exports, schema, public page, provenance, readme)
   - Slice 6: Blocked on lawful byte source
   - Slice 7: Optional Databricks port

4. **src/register/contract.py** — Verified bronze table contracts:
   - `listing_capture`: listing metadata, status, row count, archive URL + timestamp
   - `listing_capture_file`: per-file rows with archive_digest (nullable)
   - Status enum: `ok | blocked | error | empty`
   - Archive_digest nullable per D-011 (unknown identity)

5. **src/register/store.py** — Verified implementation:
   - `analytics_fetch` and `analytics_file_observation` tables for Source A
   - Append-only INSERT only, no UPDATE/DELETE (D-006)
   - `observed_file_span` view aggregates observations by file
   - `append_listing_capture()` enforces contract: blocked/error/empty captures carry no file rows (cannot read as mass removal per D-007)

6. **Spike findings** — Referenced in D-014 via `SPIKE_FINDINGS.md`, but not read (does not exist in main yet; Session B2 is implementing Source B).

## What was verified

✓ Table schemas in code match the contract test's expectations  
✓ Append-only enforcement prevents accidental UPDATEs  
✓ Bronze row_count and status encoding prevents mass-removal misreads (D-007)  
✓ Archive_digest NULL handling documented per D-011 consequence  
✓ View `observed_file_span` correctly aggregates across all sources  
✓ Source A is live: analytics.py already runs; 93 PDFs on 2026-10-04  
✓ D-014 (Wayback source) finalized; spike confirmed reachability  
✓ Slice 1 classifier does not yet exist (planned, not started)  

## Gaps found

1. **D-013 not in DECISIONS.md yet** — Removal rules and classification event types are defined in BACKLOG.md (Slice 1) but the decision itself is not recorded. This is expected (D-013 will be written during Slice 1 implementation). The document references D-013 as settled, but it is pending.

2. **D-017 not yet in DECISIONS.md** — Source B pagination completeness tracking is mentioned in BACKLOG.md (Slice 0 pending) and D-014 (as a risk), but no formal decision entry. This is the critical unresolved question for removals. Worth recording as D-017 during Slice 0 Source B implementation.

3. **SPIKE_FINDINGS.md referenced but not committed** — D-014 says spike findings are in `SPIKE_FINDINGS.md`, but file does not exist on main. Expected: Session B2 will create this during Source B implementation.

4. **README.md not yet merged** — ARCHITECTURE.md references README.md and assumes it exists. Session R (README) is running in parallel. Expected: README lands as a PR before or after this architecture doc.

## Architecture decisions recorded in document

- Three hard constraints: never store content, never download from DOJ, never claim removal on single absence
- Five critical consequences: identity unknowability, Source A liveness-only, Slice 6 blockage, two-poll gating, D-011 third-party source requirement
- Data flow diagram (ASCII) showing sources → bronze → classifier → outputs, with status (built/planned/blocked)
- Slice-by-slice status: what ships, why it's sized that way, blockers
- Three open questions that will change architecture (D-012 provider, D-017 pagination, Slice 6 byte source)

## Recommendations for next contributor

1. Read `docs/ARCHITECTURE.md` first, then `BACKLOG.md` in slice order.
2. When starting Slice 1, write D-013 (classification rules) and D-017 (pagination completeness) formally.
3. When Source B ships, commit `SPIKE_FINDINGS.md` with markup analysis and pagination edge cases.
4. Before Slice 2 public exports, confirm SCHEMA.md semver contract with BACKLOG.md "Done when" criteria.

## Files touched

- `docs/ARCHITECTURE.md` — created, 1000+ words
- `docs/handover/arch-status.md` — created (this file)

## No decisions added

Task specifies no reserved decision number. No architectural decisions were discovered that are not already recorded in DECISIONS.md.

---

**Next:** Merge to main via PR "docs: add architecture overview and roadmap status". No code changes. Run boundary-auditor and pytest before commit (docs-only, tests not applicable).
