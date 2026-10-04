# Pre-commit Hook Setup

A pre-commit hook runs local mechanical checks before you commit (conflict markers, decision IDs, schema drift), catching errors locally instead of at PR review. This is optional but recommended. It does NOT run the full boundary-auditor — that happens at PR time.

## Setup

**One-time, in your worktree:**

```bash
cd /path/to/epstein-worktree
cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

The hook is a script that runs fast local tests on staged changes. It checks:
- Merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
- Decision ID uniqueness and ordering (no duplicates or gaps)
- Table schema drift (DDL matches contract)
- Orphaned decision references in source code
- Bronze append-only property (no UPDATE/DELETE in code)

It will report violations with file and line numbers, block the commit if found, and let it through if everything passes.

## Using it

After `git add`, just run `git commit` as normal. The hook runs automatically:

```bash
git add src/register/classifier.py
git commit -m "feat(s1): add completeness gating"

# If hook finds violations:
# [pre-commit] Hygiene checks failed.
# Fix the issue, then git add and git commit again.

# If all clear:
# [pre-commit] ✓ hygiene checks pass
# [main abc1234] feat(s1): add completeness gating
```

## Skipping the hook (rare)

If you need to bypass it (e.g., a temporary debug commit):

```bash
git commit --no-verify -m "wip: debug classifier"
```

**Do not push with `--no-verify` to main.** The post-merge CI checks will catch it.

## Troubleshooting

**"permission denied" on .git/hooks/pre-commit:**
```bash
chmod +x .git/hooks/pre-commit
```

**Hook doesn't run:**
- Verify it exists: `ls -la .git/hooks/pre-commit`
- Verify it's executable: `chmod +x .git/hooks/pre-commit`
- Check the shebang line: should be `#!/bin/bash`

**Hook times out:**
- The tests can be slow on large diffs. If you hit a timeout, split your commit into smaller pieces.

## What it checks

The hook runs two test suites that are fast and do not require a Claude session:

1. **test_repo_hygiene.py:**
   - No merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
   - Decision IDs are unique, ascending, and contiguous (no gaps like 013, 015, 016)
   - All D-NNN references in code exist in DECISIONS.md
   - Table schemas match their contract definitions

2. **test_contract.py:**
   - listing_capture and listing_capture_file tables exist and match expected columns
   - Non-ok captures cannot carry file rows
   - Bronze tables are append-only (no UPDATE/DELETE/TRUNCATE in source code)

**What it does NOT check:** The full hard boundaries (B1–B7) from CLAUDE.md. That still requires the boundary-auditor subagent, which you run at PR time:
```bash
uv run pytest
# then open the PR and tell the coordinator to review it
```

The pre-commit hook catches the mechanical errors (conflicts, ID gaps, orphaned refs) that would block review. The boundary-auditor catches the architectural violations (document content, media datasets, etc.).
