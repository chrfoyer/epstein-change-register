# Compaction protocol

Compaction summarises a session's context. A summary can drop the worktree path,
the branch, the reserved decision number or the shared rules, which is how a
session starts editing the wrong tree. Every parallel session follows this.

1. **Compact only at a clean checkpoint.** Everything committed, branch pushed,
   no half-edited file, no pending review request from the coordinator. Never
   compact mid-edit.
2. **Write the status file first.** `docs/handover/<name>-status.md`: worktree
   path, branch, reserved decision number, done, next, open questions, and
   anything the coordinator told you. Commit it. Do not edit `BACKLOG.md`.
3. **Keep these in the summary.** The absolute worktree path (edit only under
   it), branch, decision number, the rules in `preamble.md`, the contract in
   `src/register/contract.py`, and any open PR number.
4. **After compacting, before any other action.** Re-read `preamble.md`, your
   `session-<name>.md` and your status file. Run `git status` and
   `git worktree list`. Restate branch and task in two lines.
5. **Stagger.** Do not compact while a PR of yours awaits review feedback.

A `SessionStart` hook in `.claude/settings.json` (matcher `compact`) prints
`preamble.md` into the session after every compaction, so the shared rules
survive even if the summary drops them. It cannot restore session-specific
state, which is what the status file is for.

The coordinator keeps its own state in `coordinator-status.md`.
