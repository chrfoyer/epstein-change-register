# Handover sessions

Prompts for running Claude Code sessions in parallel. One coordinator session
reviews and merges; the others each own one branch in their own worktree.

## Start a session

```
uv run python scripts/new_session.py a feat/s1-change-classifier
```

Open Claude Code in `../epstein-a`, then run `/session-start a`. The slash command
reads `preamble.md` plus `session-<name>.md`.

## Sessions

| Name | Task | Branch | Decision no. |
|---|---|---|---|
| a | Slice 1 change-event classifier and report | `feat/s1-change-classifier` | D-013 |
| b | Slice 0 Source B, Wayback listing captures | `feat/s0-wayback-source` | D-014 |
| c | Research and docs: Jev terms, community repo, LIMITATIONS.md | `docs/s2-limitations-and-research` | D-015 |

## Coordination rules

- Each session works only under its own worktree path. Never edit files under
  another worktree, including the coordinator's.
- Shared table contracts live in code (`src/register/contract.py`) and are
  checked by `tests/test_contract.py`. Change the contract in its own PR.
- Do not edit `BACKLOG.md` from a session branch. Put status in
  `docs/handover/<name>-status.md`; the coordinator folds it in after merge.
- Merge order: contract and schema PRs first, then dependents.
- If you find a collision or a contradiction, stop and report it rather than
  resolving it silently.
