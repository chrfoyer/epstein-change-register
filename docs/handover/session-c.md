# Session C: research and docs

Branch `docs/s2-limitations-and-research`. Decision number D-015. Docs only. Do not
call any model API, hold or request any key, or post anything publicly.

1. **Jev preconditions (D-012).** Read TypeSafe's legal pages
   (`docs.typesafe.ai/legal.md` links the Privacy Policy, DPA and MCA),
   `docs.typesafe.ai/model-jaggedness/jev-1.13.md`, and OpenRouter's provider-logging,
   data-collection and ZDR guides. Amend D-012 with what is confirmed (cite page and
   section, paraphrase), what is still unknown, and a recommendation between direct
   TypeSafe (`v1/systemone`) and OpenRouter (`alpha/decisions`). The maintainer has
   accounts and credits on both.
2. **Community repo.** Read `yung-megafone/Epstein-Files` issues #7, #27, #24, #28,
   #34, #30 and #11, including comments. Write `docs/community-repo-notes.md`: what
   they want from change tracking, what we can supply, what we should not touch (no
   license; torrent mirrors, see D-002 and D-003). Draft, but do not post, a comment
   for #27 offering a Parquet change feed. The maintainer posts it.
3. **`LIMITATIONS.md` first draft** (BACKLOG Slice 2): the bot wall and age gate
   (D-011), Source A's top-100 bias, observation time versus publication time, no
   document hashes, Slice 6 blocked, claimed versus measured hashes. Cross-reference
   D-ids.
4. **Draft a message to DOJ's web or FOIA contact** asking for an allowlist or a
   machine-readable file manifest for the court-record datasets. Find the public
   contact path first. Contact details in the draft are the repo issues URL only.
   The maintainer sends it.

Deliver the four documents on one branch, plus `docs/handover/c-status.md`. Use
D-015 only if a real decision emerges.
