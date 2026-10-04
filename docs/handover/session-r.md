# Session R: repo README and licence proposal

Branch `docs/s5-readme`. Decision number D-018. Start with `/session-start r`. Docs
only; no code, no network access beyond reading this repo and `gh run list`.

## 1. README.md (root)

The repo has none. Someone with 60 seconds should be able to say what it is. Order:
problem, what it is and is not (it hosts no documents, D-003), architecture,
current status, how to run, where to read more.

- **Architecture diagram** (Mermaid in the README): Source A, B, C, bronze tables,
  classifier, published outputs. Mark every box **built**, **in progress** or
  **planned**. Only call something built if it is on `main` and you have seen it run.
- **Status table by slice**, taken from `BACKLOG.md` and `docs/handover/coordinator-status.md`.
- **How to run**: `uv sync`, `REGISTER_CONTACT`, `uv run pytest`, the Source A command.
  Run each command you document and paste the real output shape, not what you expect.
- **Cost per run**: measure from `gh run list --workflow crawl.yml` durations; state
  the number and that it is on public-repo free minutes. Do not estimate.
- **CI badge**, links to `docs/LIMITATIONS.md`, `DECISIONS.md`, `docs/handover/`.
- Lead with the honest limits: observation is not publication, Source A is a top-100
  sample, nothing downloads from justice.gov (D-011). Do not oversell.
- No screenshot yet; Slice 3 has none to show.

## 2. Licence proposal (do not add a LICENSE file)

A public repo with no licence is "all rights reserved". Write D-018 as a *proposal*:
options for the code (MIT, Apache-2.0) and for the published metadata (CC0, CC BY 4.0),
what each implies for reuse and attribution, and a recommendation. This is not legal
advice; say so. The maintainer chooses, and a follow-up adds the file.

## Rules specific to this task

- Every claim in the README must be checkable against the repo or a run. If you
  cannot verify it, leave it out or mark it planned.
- Never use a personal email; the contact is the repo issues URL.
- Do not edit `BACKLOG.md`. Write `docs/handover/r-status.md`.
