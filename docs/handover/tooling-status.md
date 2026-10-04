# Tooling Session Status

**Branch**: chore/review-loop-robustness  
**Status**: Complete, ready for merge  
**Deliverables**: Enhanced repo hygiene tests, post-merge CI, pre-commit hook documentation

## What is done

### 1. Expanded `test_repo_hygiene.py` (3 new checks)

- **Decision contiguity**: IDs are unique, ascending, and in order (no gaps). Allows reserved-but-unused numbers (e.g., D-015).
- **Decision references**: All D-NNN citations in source code exist in DECISIONS.md. Docs are excluded (they may reference planned decisions).
- **Table schema drift**: Verifies that table DDLs in contract.py match the actual schema expected columns. Catches accidental column renames or type changes.

All 34 tests pass.

### 2. Post-merge verification (`.github/workflows/post-merge.yml`)

A new CI job runs after every merge to main:
- Runs `test_repo_hygiene.py` and `test_contract.py` on the merged state
- Reports success if all invariants hold
- Blocks main from ending in an invalid state

This catches accidents that CI on the PR might have missed (e.g., a conflict marker that slipped through rebase).

### 3. Pre-commit hook documentation and script

- **`docs/PRE_COMMIT_SETUP.md`**: Setup guide for sessions to install a local pre-commit hook
- **`scripts/pre-commit`**: Hook script that runs fast checks before allowing a commit
  - Runs `test_repo_hygiene.py` and `test_contract.py` locally
  - Catches conflict markers, decision ID gaps, orphaned refs, schema drift before commits

Sessions can opt-in: `cp scripts/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`

## Test results

```
tests/test_repo_hygiene.py (4 tests) PASSED
tests/test_contract.py (9 tests) PASSED

13 tests; 34 total with parametrize
```

## What this enables

1. **Mechanical errors caught early**: Conflict markers, decision gaps, orphaned references are visible in pre-commit or post-merge CI, not at review time.
2. **Schema safety**: Table definitions are checked against their contract. Accidental schema changes are caught.
3. **Cleaner reviews**: Coordinator can focus on architectural violations (boundary-auditor), not mechanical issues.
4. **Auditability**: Every main commit is verified valid; no orphaned references or merge artifacts slip through.

## What is not included

- Full boundary audit (B1–B7 checks) — that still requires the boundary-auditor subagent at PR review time.
- This tooling is *complementary* to the boundary-auditor, not a replacement.

## Next steps

1. Merge this PR
2. Sessions can opt-in to pre-commit hook (documented in docs/PRE_COMMIT_SETUP.md)
3. Main is now protected by post-merge CI
