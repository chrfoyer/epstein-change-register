# Shared preamble

You are continuing work on the epstein-change-register repo (GitHub:
chrfoyer/epstein-change-register, public). Read `CLAUDE.md`, `DECISIONS.md` and
`BACKLOG.md` before anything else. They are authoritative; if a request conflicts
with them, say so and ask.

## State

- Slice 0 Source A (analytics.usa.gov top-downloads CSV, ~100 rows) runs daily at
  05:17 UTC on GitHub Actions. State is Parquet on the orphan `data` branch.
- D-011: we never download from justice.gov. PDFs sit behind an age gate and the
  listings behind an Akamai bot check. Slice 6 is blocked by that.
- D-012 (Jev) is proposed only. Nothing external-API is implemented.
- Shared listing tables are defined in `src/register/contract.py` and written
  with `store.append_listing_capture`. Do not define them anywhere else.

## Rules

- Work only in your own worktree (`scripts/new_session.py`), and only through
  absolute paths under it. Never edit files under another worktree.
- Branch names follow D-010. Merge by PR with "Create a merge commit". `main` is
  protected and requires the `test` check. Rebase on `origin/main` first.
- Run `uv run pytest` and the boundary-auditor subagent before every commit.
  Report actual output.
- Never put document content, recovered redaction text, or anything from
  `data/restricted/` into a file, log, fixture or commit. Send nothing to an
  external API except the sources named in your task. Never pass an age gate or
  bot check.
- Requests to third parties are serial, with a delay. The User-Agent contact comes
  from the `REGISTER_CONTACT` environment variable (the repo issues URL). Never use
  the maintainer's personal email. Do not paste, print or commit API keys.
- Commits are Conventional Commits scoped by slice, with a `Refs: D-0NN` trailer
  when a decision is touched, ending with the Co-Authored-By trailer given in your
  session instructions.
- Use only your reserved decision number, and only if a real decision is made.
  Record the rejected alternative.
- Do not edit `BACKLOG.md`; write `docs/handover/<name>-status.md` instead.
- End with a commit that runs. Do not leave a branch open across a gap.
