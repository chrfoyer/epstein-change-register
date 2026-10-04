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

<!-- Template for new entries:

## D-00N — <one-line decision>

**Decided:**

**Rejected:**

**Why:**

**Would change if:**

-->
