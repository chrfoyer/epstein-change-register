# Coordinator status

As of 2026-10-04 (evening). The coordinator reviews and merges; it builds only tooling.

## Sessions

| Session | State |
|---|---|
| A (`D:\epstein-s1`, `feat/s1-change-classifier`) | Running. Branch pushed, rebasing on `origin/main`; told to wire `complete_by_source` into the removal rule, add fixtures for it, then open the PR. Review against D-013 and the completeness rule. |
| B spike | Done and closed. PR #6 and #9 merged. D-014 and `SPIKE_FINDINGS.md` on `main`. |
| B2 implementation | Not started. Prompt: `docs/handover/session-b2.md`, D-017. |
| C | Done and closed. PR #4 merged, then corrected by #8. |

Merged so far: PRs #1 to #9. Worktrees for B and C are removed.

## Open items

- Review A's PR when it opens: identity order, NULL digest means unknown, removal
  only when both listings are explicitly complete, Source A never produces
  added/removed/moved, report wording.
- Start session B2 (Source B implementation). Its first step may be a small
  contract PR for a `partial` status; A does not depend on it.
- Source A daily crawl: first unattended run was due 2026-10-05 05:17 UTC. Confirm the
  `data` branch grew and the run was green. Slice 0 is done after three green runs.
- D-012: choose direct TypeSafe (documented `v1` endpoint, one set of terms) or
  OpenRouter (`alpha` path, existing credits). C recommended OpenRouter; the
  coordinator leans direct TypeSafe. The maintainer decides, then amend D-012.
- Move Claude's scratch folder to D: with a junction once every Claude session is
  closed, including the coordinator (`C:\Users\chrfoyer\AppData\Local\Temp\claude`
  to `D:\claude-temp`). User-level `UV_CACHE_DIR`, `UV_PYTHON_INSTALL_DIR` and
  `npm_config_cache` already point at `D:\cache`; clear the old C: caches after all
  sessions restart.
- DOJ outreach (`docs/DOJ-contact-draft.md`) and the issue #27 comment draft in
  `docs/community-repo-notes.md` are the maintainer's to send or post. The DOJ contact
  is unverified.
- Redesign the PR-review hook as a command hook (agent hooks ignored `if` and could
  not run `gh` or `git`).
- Fold session status into `BACKLOG.md`: Source B spike done, Slice 6 blocked, Slice 1
  pending A's PR.

## Facts worth keeping

- Never use the maintainer's personal email in any request or doc.
- `REGISTER_CONTACT` is the repo issues URL.
- `main` is protected; merge by PR with a merge commit; `test` must pass. Always pass
  the PR number to `gh pr checks` and `gh pr merge`.
- Wayback's CDX digest is a base32 SHA-1, never sha256.
- Another session once wrote into the coordinator tree; use only absolute paths under
  your own worktree.
