# Decision Log

Lightweight ADRs. One entry per significant decision. The point is to record the
**alternative that was rejected and why** — that is what makes this readable to
someone reviewing the project later, including future me.

Format: what was decided, what else was considered, why, and what would change
the answer.

---

## D-001 — Track changes prospectively, not retrospectively

**Decided:** poll the DOJ library on a schedule and build the change history
forward from day one.

**Rejected:** reconstructing history from Internet Archive captures and
community mirrors.

**Why:** retrospective reconstruction depends on third-party snapshots with
inconsistent coverage and messy provenance, and would consume the whole project
before producing anything. Prospective watching yields a defensible feed after
one week, with provenance I generated myself.

**Would change if:** a well-provenanced complete historical snapshot becomes
available.

---

## D-002 — Scope to court-record and disclosure PDFs; exclude image and video sets

**Decided:** the register covers text-native PDF datasets only.

**Rejected:** full-corpus coverage.

**Why:** three reasons, any one sufficient. The media sets contain forensic
imagery and seized pornographic material — DOJ age-gates the repository for this
reason — which creates real legal exposure under Danish and EU law for anyone
processing or redistributing it. The PDFs are also where the re-release churn
actually happens, so they carry most of the signal. And bounded scope is what
makes the project finishable at one block per week.

**Would change if:** nothing foreseeable. This is a hard boundary, not a
prioritisation call.

---

## D-003 — The register does not host documents

**Decided:** store metadata, hashes, and provenance; link to DOJ and to archive
snapshots for the documents themselves.

**Rejected:** mirroring the corpus.

**Why:** hosting means republishing material that includes inadvertently
unredacted victim identities. It also means storage cost, bandwidth, and a
takedown surface. Metadata-only keeps the dataset small enough to version in a
repo and sidesteps the entire question.

---

## D-004 — Failed-redaction findings are public; failed-redaction content is not

**Decided:** detect recoverable redactions by comparing the embedded PDF text
layer against OCR of the rasterised render. Publish the *geometry and fact* —
page, bounding box, character count, detected entity type. Route the *content*
to a separate schema with distinct grants.

**Rejected:** (a) not detecting it at all; (b) publishing what was recovered.

**Why:** naive text extraction pulls the supposedly-redacted content into the
pipeline by default — this is not opt-in, it is what `pdftotext` does. Ignoring
it means silently republishing protected identities into any downstream index.
Publishing it means doing so deliberately. Detecting-but-segregating is the only
option that is both honest about what the corpus contains and safe.

**Would change if:** the detection proves unreliable enough that the findings
mislead — in which case drop the feature entirely rather than ship it hedged.

---

## D-005 — DuckDB first, Databricks only if justified

**Decided:** build on DuckDB + a scheduled job; treat the Databricks port as
optional.

**Rejected:** starting on Databricks.

**Why:** the change register is thousands of rows, not billions. Databricks'
genuine advantages here — Unity Catalog governance, Auto Loader, OCR at scale —
only bind at full-corpus scale, which D-002 explicitly rules out. Starting on
managed infrastructure would add cost and iteration friction for capability the
POC does not need.

**Would change if:** scope expands to full-corpus OCR, or the governance split
in D-004 turns out to be materially easier to demonstrate with Unity Catalog
than with filesystem permissions.

---

## D-006 — Bronze is append-only; do not rely on Delta time travel for history

**Decided:** model the corpus history as explicit rows with a `capture_ts`
column.

**Rejected:** using table version history as the historical record.

**Why:** `VACUUM` deletes the files time travel depends on — default retention
is seven days. Time travel is a recovery mechanism for pipeline bugs, not an
archival guarantee. Anything that needs to be citable in two years must be
modelled data.

---

## D-007 — "Removed" requires two consecutive absences and third-party evidence

**Decided:** a removal event fires only after a file is absent from two
consecutive polls, and must cite an archive capture proving it was previously
live.

**Rejected:** emitting a removal on first absence.

**Why:** a flaky listing page, a rate-limit response, or a re-upload under a new
filename all look like a removal on a single poll. Publishing "DOJ deleted this"
on that evidence would be wrong often enough to discredit the whole register.
The claim the project makes must be narrower than the claim readers want.

---

## D-008 — Cost posture: opusplan, subagents on Haiku, no aggressive fan-out

**Decided:** Opus plans, Sonnet executes (`opusplan`); subagents are routed to
Haiku.

**Rejected:** (a) all-Opus; (b) aggressive subagent fan-out.

**Why:** the bottleneck is one 4–6h block per week, not model throughput.
Parallel subagents start cold and are a usage driver, not a saving.

**Would change if:** Slice 6 parameter sweeps become the dominant workload,
where fan-out genuinely compresses wall-clock time.

---

## D-009 — Restricted content at `data/restricted/**` with a Read deny rule

**Decided:** restricted content lives at `data/restricted/**`, enforced by a
Claude Code `Read` deny rule in `.claude/settings.json`.

**Rejected:** relying on convention alone.

**Why:** D-004 is only as strong as what enforces it. A deny rule makes the
separation structural rather than something the maintainer has to remember at
23:00 while debugging.

**Would change if:** the storage layout moves, in which case the deny rule path
moves with it in the same commit.

---

## D-010 — Trunk-based with short-lived branches, `--no-ff` merges, slice tags

**Decided:** `main` is always releasable. Work happens on one short-lived branch
per backlog item, named `<type>/s<slice>-<slug>`, merged with `--no-ff`.
Commits use Conventional Commits scoped by slice, with `Refs: D-00N` trailers.
Completed slices are tagged `slice-N-done`.

**Rejected:** (a) GitFlow (`develop`/`release` branches); (b) committing directly
to `main`; (c) squash merges.

**Why:** GitFlow solves parallel releases and multiple contributors, neither of
which exists here. Direct commits lose the grouping that makes history
answer "what did Slice 1 change?". Squashing discards the per-commit
boundary-audit granularity; `--no-ff` keeps both the detail and the unit.
Slice scope, decision trailers and tags tie every change back to `BACKLOG.md`
and `DECISIONS.md`, which is the traceability goal.

**Would change if:** a second contributor joins (add PR review and required
status checks) or the register starts cutting versioned dataset releases (add
release tags per `SCHEMA.md` semver).

**Amended 2026-10-04:** the repo is on GitHub, so `main` is now protected:
required `test` status check, no direct pushes, no force-push or deletion, merge
commits only. Merges happen through pull requests ("Create a merge commit"),
which keeps the `--no-ff` shape. Required checks make a local merge-and-push
impossible, which is the point: the gate is enforced, not remembered.

---

## D-011 — Observe via third-party sources; never download from justice.gov

**Decided:** Slice 0 records observations from sources that are not
justice.gov itself: (A) the analytics.usa.gov DOJ top-downloads CSV, (B) Wayback
listing captures and CDX digests when archive.org is reachable, (C) community
hash lists as claimed hashes with their source. Only court-record PDFs under a
numbered `DataSet N/` path are recorded; media and prior-disclosure folders are
excluded by an allow-pattern, not a blocklist (D-002). `sha256` of documents is
null until a legitimate byte source exists; `archive_digest` is the interim
fingerprint.

**Rejected:** (a) headless browser or scripted age-gate/bot-check passing;
(b) polling justice.gov directly, as D-001 assumed; (c) in-memory download and
hash of PDFs.

**Why:** recon found the listing behind an Akamai JS challenge that answers
HTTP 200, and PDF URLs 302 to `/age-verify`. Passing either means defeating
access controls DOJ put in place for sensitive material, which conflicts with
boundary 5 and D-002. A bot-wall page must be recorded as `unexpected`, never as
an empty listing, or it reads as mass removal (D-007).

**Limits:** analytics data is DOJ's own, so it is liveness evidence but not
independent of DOJ. It covers only the ~100 most-downloaded files, so absence
from it means nothing. Observation time is not publication time.

**Would change if:** DOJ offers an allowlist, API, or feed; or the age gate and
bot check are removed.

---

## D-012 — Jev as an optional, advisory, metadata-only classifier (Proposed)

**Status:** proposed, not implemented. Not before Slice 1.

**Decided:** TypeSafe's Jev (a hosted "System One" model returning typed
answers with calibrated confidence) may be used at three points, always on
allowlisted metadata, always advisory:
1. **Scope gate** for new DOJ site sections or paths (community issues #24 and
   #28 report DOJ adding sections): classify "court-record PDFs" vs "media".
   Output is a suggestion for human review; the D-002 allow-pattern stays the
   hard filter.
2. **Anomaly triage** on observation metadata, confidence-gated: a low-confidence
   or high-anomaly answer raises a flag for review and never emits a change event.
3. **Card text** (Slice 3): plain-language wording generated from change events.

Every call is logged to an append-only `llm_decision` table (`capture_ts`,
`source_url`, question id, input fields, answer, confidence), because the model
is not deterministic and results must be reproducible after the fact.

**Rejected:** (a) Jev inside the change-event classifier or the D-007 removal
rule, which stay deterministic and fixture-tested; (b) sending page text, OCR
output, or anything from `data/restricted/` (D-003, D-004); (c) a frontier LLM
for these calls, since they are bounded yes/no or pick-one judgments.

**Why:** the fit is real: these are cheap, bounded judgments. Vendor-claimed
pricing is $0.042 per million input tokens with 70–500 ms latency, unverified by
us. But an external API is a publication channel, and TypeSafe's launch post says
nothing about retention or training use.

**Preconditions before any implementation:**
- written data retention and training terms from TypeSafe;
- access: the model is early-access signup only, so the code must work with it
  disabled, and disabled is the default;
- API key as a GitHub Actions secret, never committed;
- an input allowlist enforced in code and covered by a test that fails on any
  non-allowlisted field.

**Would change if:** terms are unacceptable, access is unavailable, or the
metadata turns out too thin to classify, in which case drop it and say so.

**Sources:** github.com/disler/ten-levels-of-jev (MIT; confidence gating and
cheap-routing patterns), typesafe.ai/blog/introducing-system-one-models-and-jev.

---

<!-- Template for new entries:

## D-00N — <one-line decision>

**Decided:**

**Rejected:**

**Why:**

**Would change if:**

-->
