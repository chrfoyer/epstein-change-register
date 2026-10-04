# What This Register Cannot Tell You

This register tracks metadata and verifiable observations from third-party sources. What it
does *not* do is listed here.

## Access Barriers

**You cannot verify file content yourself via this register** (D-011, Slice 6 blocked)

DOJ PDFs sit behind an age gate and an Akamai bot-check that we do not attempt to pass.
The register observes that files exist, where they move, and what metadata is available.
It cannot download file bytes, compute SHA-256 hashes of the PDFs themselves, or detect
redaction changes over time.

**Consequence:** The register offers `archive_digest` (SHA-256 from Wayback captures when
available) as a fallback identity for files without a Bates number, but the digest may be
stale or missing. Document identity is unverified; true content fingerprints remain unknown.
Slice 6 (redaction-coverage tracking) is explicitly blocked pending a lawful byte source
(DOJ feed, official allowlist, or verified Wayback captures).

## Observation vs. Publication Time

The register records *when it observed* a file, not when DOJ published it.

A file that first appears in an observation on October 4 was released *by or before*
October 4, but could have been live for days or weeks before we started polling. The
observation carries a capture timestamp, not a publication date. Do not interpret
first-appearance as publication.

**Consequence:** For historical claims ("DOJ released X on date Y"), cross-reference with
your own archive snapshots or DOJ announcements. The register can only say "as of date Z,
this file was in the listing."

## Source Limitations

### Source A: analytics.usa.gov top-downloads CSV (Slice 0, live)

The CSV reports DOJ's own top ~100 most-downloaded files. Absence from it proves nothing;
it is a liveness signal for a subset, not a complete inventory.

- **Bias:** Only the 100 most-downloaded files are recorded. Files that are live but rarely
  accessed do not appear.
- **Scope:** Limited to files DOJ reports in their analytics export; coverage may shift
  when DOJ changes how analytics are published.
- **Cannot claim "removed":** A file dropping out of the top 100 is not removal—it may
  simply be less popular. Removal claims require Source B (Wayback comparisons) plus
  third-party evidence (D-007).

### Source B: Wayback listing captures and CDX digests (Slice 1, blocked)

Internet Archive provides snapshots of listing pages and a CDX index of URLs they have
captured. This source enables before/after comparisons on complete listings.

- **Status:** Archive.org was offline on October 4, 2026. Integration is pending availability
  and CDX API stability. See Slice 0 backlog item "Source B."
- **Dependency:** CDX lookups are slow and Archive.org's IP blocks are common. The register
  is designed to cache aggressively and never hammer the archive.
- **Caveat:** Archive coverage is not uniform. Some URLs are captured; others are not. A
  missing Wayback capture does not mean a file is new.

### Source C: Community hash lists (Slice 0, not yet integrated)

Community members may contribute hash lists and metadata from their own archives or from
historical records (Reddit, forum posts, prior torrents).

- **As-claimed:** Hashes are stored with their source and capture date, but not independently
  verified by the register. "Claimed hash" ≠ measured truth.
- **No re-distribution:** The register does not host or reseed torrents or archives. It
  records metadata only.
- **Provenance:** Each hash carries a source label so you can trace it. Verification is your
  responsibility.

## Document Scope

**The register covers court-record and disclosure PDFs only** (D-002)

- **Excluded:** Image datasets (forensic photos, evidence) and video datasets. These sit
  behind an age gate for legal reasons; the register does not ingest them.
- **Included:** Text-native PDFs under numbered `DataSet N/` paths, and court-record filings.
- **Not included:** Media pages, administrative pages, or non-PDF documents unless they are
  formal disclosures or filings.

**Consequence:** You can track changes to the PDF inventory. You cannot track media, images,
or non-PDF documents through this register.

## Redaction and Recovered Content

**File identity depends on Bates numbers and archive digests** (D-011, D-013)

When a Bates number is present in the listing, it is the primary identity. When missing,
the register falls back to `archive_digest` (SHA-256 from Wayback). When both are missing,
identity is unknown.

- **No "changed" claim without fingerprint:** If identity is unknown (no Bates, no archive
  digest), the register will not claim a file was "reuploaded" or "changed," even if the
  same URL now resolves to different content. A flag will be raised instead (D-007).
- **Claimed vs. measured hashes:** Community submissions may include SHA-256 hashes; these
  are stored as `claimed_hash` with source and date. The register cannot compare claimed
  hashes to measured hashes without PDF bytes (blocked by D-011). Mismatches are noted but
  not resolved.

**Recovered redaction findings are not published** (D-004)

When the register eventually detects recovered redactions by comparing embedded PDF text to
OCR of a rendered page (Slice 6), the *findings* (page number, bounding box, character count)
will be public. The *content* (what was recovered) will be stored separately under restricted
grants.

**Current status:** Slice 6 is blocked indefinitely (D-011 blocker). Recovered-redaction
detection is not implemented.

## Removed Files: the Two-Poll Rule

A file is marked `removed` only after:
1. Absence from two consecutive complete polls (via Source B: Wayback snapshots), AND
2. Third-party evidence that the file was previously live (an archive capture proving it existed).

**Not removed:**
- A file absent from only one poll.
- A file that appears to be absent but the source returned an error or unexpected status.
- A file that dropped out of the top 100 in Source A (that is a decline in popularity, not removal).

**Consequence:** Removal claims lag behind actual removals by the interval between polls.
A file deleted today may not be marked removed for weeks. Early removal claims are withheld
to avoid publishing false positives (D-007).

## What Is Known at Cold Start

On the first run, the register has no historical data. It can only observe what exists today.

- **No "added" events on day one:** Files in the first poll are recorded as observations, not
  as `added` events. `added` is only emitted when a file appears *after* a prior complete poll.
- **No "removed" events on day one:** There is no prior observation to compare against.
- **Archive digests available only where Wayback has captures.** If a file was never
  captured by Archive.org, `archive_digest` is null, and identity falls back to Bates number.

**Consequence:** The register's output grows more complete and confident with elapsed
observation time. The first week's report is incomplete. After one month of daily polling,
claims are firmer. After three months, the register can support removal events and re-upload
tracking.

## Data Quality and Cost

**Source completeness and quality depend on external services**

- Analytics.usa.gov data depends on DOJ updating and publishing their analytics. Changes to
  DOJ's analytics export can break the source.
- Wayback availability depends on Archive.org's uptime and IP block policies.
- Community contributions depend on volunteer participation and archival effort.

**The register does not validate the source's data before storing it**

When DOJ's listing page returns an unexpected status or empty result, the register records
`status: unexpected` or `status: empty`, not `removed`. The listing may have been flaky or
momentarily unavailable. You must interpret the raw `status` field.

## What Gets Published and What Doesn't

### Public tables (published weekly as Parquet + CSV)

- `change_event`: the typed change log (added, removed, reuploaded, moved).
- `listing_capture`: observation metadata (timestamp, source, status, file count).
- `listing_capture_file`: each file observed (URL, Bates number, archive digest).
- `llm_decision` (when Jev is enabled): scope gates and anomaly triage (metadata only;
  no prompt or response content).

### Not published

- Recovered redaction content (restricted storage under D-004 grants).
- Full PDF bytes or file content.
- User API keys or credentials.

### Also available (on the data branch, not published as Parquet)

- Source A: Raw analytics.usa.gov CSV exports on each run.
- Raw Wayback CDX digests (when Source B is enabled).
- Community submissions (when Source C is enabled), with source labels.

## Getting Current

This register is one data point, not the ground truth.

- **Cross-reference with archive snapshots.** Use archive.org's Wayback Machine to independently
  verify file existence and content on specific dates.
- **Monitor DOJ announcements.** The register cannot tell you when DOJ planned a release or
  removed files deliberately. Check official DOJ statements for context.
- **Use this as a change log, not a inventory.** The events listed show what changed between
  observations. For an absolute inventory, compare your own snapshot against the register's
  latest observation.

---

**References:** D-002, D-003, D-004, D-007, D-011, D-013 in [DECISIONS.md](DECISIONS.md)
