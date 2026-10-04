# Coordinator status

As of 2026-10-04. The coordinator reviews and merges; it builds only tooling.

## Sessions

| Session | Worktree | Branch | State |
|---|---|---|---|
| A | `D:\epstein-s1` | `feat/s1-change-classifier` | committed `fcf6e12`; no PR yet |
| B | `D:\epstein-wayback-source` | `feat/s0-wayback-source` | committed `b6cef6b`; no PR yet |
| C | `D:\epstein-limitations` | `docs/s2-limitations-and-research` | PR #4 open, changes requested |

## Open items

- Re-review PR #4 after session C's fixes (SHA-1 vs SHA-256 digest, unbuilt
  features stated as current, unverified DOJ contact details, missing
  provider recommendation and #27 draft, c-status.md).
- Review A and B PRs when they open. Check they use `store.append_listing_capture`
  and do not redefine the listing tables; BACKLOG is folded in by the coordinator.
- Source A daily crawl: first unattended run was due 2026-10-05 05:17 UTC; confirm
  the `data` branch grew and the run was green.
- D-012: decide direct TypeSafe vs OpenRouter once session C recommends.
- Move Claude's scratch folder to D: with a junction once every Claude session is
  closed (`C:\Users\chrfoyer\AppData\Local\Temp\claude` to `D:\claude-temp`).
  User-level `UV_CACHE_DIR`, `UV_PYTHON_INSTALL_DIR` and `npm_config_cache` already
  point at `D:\cache`; old C: caches can be cleared after all sessions restart.
- Redesign the PR-review hook as a command hook (agent hooks ignored `if` and
  could not run `gh` or `git`).
- Possible follow-up: record in the `archive_digest` docs that Wayback's digest is
  base32 SHA-1, not SHA-256.

## Facts worth keeping

- Never use the maintainer's personal email in any request or doc.
- `REGISTER_CONTACT` is the repo issues URL.
- `main` is protected; merge by PR with a merge commit; `test` must pass.
