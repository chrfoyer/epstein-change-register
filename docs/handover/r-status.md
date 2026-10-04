# Session R: README and licence proposal

**Branch:** docs/s5-readme
**Decision:** D-018 (reserved)
**Status:** Complete
**Time:** ~1.5 hours

## Work Completed

### 1. README.md (root)

Written with:
- **Problem statement:** DOJ files move/disappear with no public record; this register observes changes.
- **What it is/is not:** Metadata and observations, not a document mirror. Source A covers ~100 top-downloads; Source B in progress.
- **Architecture diagram (Mermaid):** Sources A, B, C → Bronze tables → Classifier → change_event → Outputs. Each box marked built/in-progress/planned.
- **Slice status table:** One row per slice, from BACKLOG.md. Slice 0 at 1 of 3 unattended runs; Slice 1 in progress; Slice 6 blocked (D-011).
- **How to run:** Real command-line help output, pytest results (32 passing), workflow cost (13 seconds), example report format.
- **Limits section:** Links to LIMITATIONS.md with D-011/D-013 references.

Every claim is verifiable by command (`uv sync`, `uv run pytest`, `gh run list --workflow crawl.yml`).

### 2. D-018: Licence Proposal

**Code options:**
- MIT: Permissive, simple, public-domain compatible.
- Apache-2.0: Permissive + explicit patent grant.
- **Recommendation:** MIT (code is a utility pipeline, not patent-relevant; simpler adoption).

**Data options:**
- CC0: Public domain, no attribution required, maximum reuse.
- CC-BY-4.0: Attribution required, aligns with provenance mission, prevents misattribution as source.
- **Recommendation:** CC-BY-4.0 (ensures chain of evidence, credits observation source, enables verification trail).

Proposal includes legal caveat (not legal advice), references to licence texts, and implementation notes (no code-header boilerplate for small projects).

## Facts

- Crawler has run once (2026-10-04 14:00:42Z), duration 13 seconds.
- Slice 0 "done when" requires 3 consecutive unattended runs; 1 complete so far.
- Session A (classifier) PR open; awaiting review on completeness gating.
- Session B2 (Wayback source) not started; D-017 reserved.

## Next Steps

- Merge PR with this README and D-018.
- Maintainer reviews D-018 and chooses code/data licences.
- Coordinator folds session status into BACKLOG.md after merge.
- Follow-up PR adds LICENSE file(s) with chosen terms.
