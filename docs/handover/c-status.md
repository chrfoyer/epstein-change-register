# Session C Status — Slice 2 Documentation

**Date:** 2026-10-04  
**Branch:** docs/s2-limitations-and-research  
**Reserved decision:** D-015 (not used; D-012 amended instead)  
**Worktree:** D:\epstein-limitations

## What is done

1. **D-012 amendment** (DECISIONS.md):
   - Expanded privacy findings from TypeSafe legal index and OpenRouter documentation
   - Confirmed TypeSafe commitment to no-training and ZDR-on-request for enterprise
   - Documented OpenRouter's opt-in data retention and per-request ZDR capability
   - Added precondition to test alpha/decisions endpoint before deployment
   - Added recommendation: prefer OpenRouter route (existing account, clearer terms, testable)

2. **community-repo-notes.md** (new file):
   - Summarized yung-megafone/Epstein-Files expectations from 7 issues (#7, #11, #24, #27, #28, #30, #34)
   - Listed what we can supply: change feeds (planned Slice 2), observation metadata, claimed hashes
   - Listed what we cannot: PDFs, torrenting, redacted content, media datasets
   - Drafted (unposted) comment for issue #27 offering Parquet feed

3. **LIMITATIONS.md** (new file, first draft):
   - Documented access barriers: age gate/bot check (D-011), Slice 6 blocked
   - Documented observation vs. publication time lag
   - Sourced Source A (top 100 bias), Source B (Wayback, now reachable), Source C (yung-megafone only)
   - Documented redaction policy: findings public, content restricted (D-004)
   - Two-poll removal rule and cold-start limitations
   - Marked features as planned (Parquet+CSV Slice 2, llm_decision Slice 3) vs current

4. **DOJ-contact-draft.md** (new file):
   - Drafted outreach message requesting machine-readable manifest, allowlist, or access policy
   - Not yet sent; for maintainer review
   - Added notes warning that FOIA may not be right channel; suggest web/IT team contact first
   - Verified contact details against justice.gov

## What is next

- PR #4 awaiting coordinator review with feedback addressed
- Once merged: handover to maintainer for executing the four tasks
  - D-012 research can inform Jev implementation (Slice 3+)
  - community-repo-notes comment to post when Slice 1 completes
  - LIMITATIONS.md to publish with Slice 1 output
  - DOJ contact message for maintainer to send via appropriate channel

## Open questions

- Whether OpenRouter's alpha/decisions endpoint actually honours ZDR; precondition to test before deployment
- DOJ's likely response to allowlist/manifest request (conservatively assume none)
- Whether TypeSafe's legal docs (URLs public but not fetched) contain material constraints

## Coordinator feedback (addressed in re-push)

- Fixed archive_digest terminology: base32 SHA-1 (CDX digest), not SHA-256
- Corrected Source B: Slice 0 (not 1), archive.org reachable (not offline)
- Clarified Source C: yung-megafone only (removed invented Reddit/forum/torrent sources)
- Marked planned features clearly (Slice 2 Parquet, Slice 3 llm_decision)
- Removed claims about current behavior not yet built (caching, flagging, claimed_hash storage)
- Fixed D-013 dangling reference
- Added TypeSafe recommendation (OpenRouter preferred)
- Added drafted comment for issue #27
- Added DOJ channel warning (FOIA may not be right path)
- Verified DOJ contact details
