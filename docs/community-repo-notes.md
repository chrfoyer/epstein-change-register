# Community Repository Notes

Based on review of yung-megafone/Epstein-Files issues #7, #11, #24, #27, #28, #30, #34, October 2026.

## What the Community Wants

**Change tracking and notification** (#27): The maintainer has built a visual diff tracker
(justice.geeken.dev and diff-tracker.geeken.dev) and wants to integrate complementary
change-event feeds. They've requested a way to template additional resources into the README.

**Hash verification and dataset consistency** (#11): A community archiver with partial datasets
wants to verify completeness and compare versions. They note mismatched hashes across DOJ
downloads, suggesting version drift over time, and have offered to share their archive metadata.

**Preservation of removed material** (#7): The project is expanding from Dataset 9 toward
identifying and recovering DOJ-hosted material that has been removed, throttled, or de-linked.
They seek existing archives, mirrors, magnets, Wayback snapshots, and partial datasets, including
court records and FOIA releases formerly linked by DOJ.

**Metadata and versioning** (#24, #28, #30, #34): Issues track upstream inconsistencies on DOJ
pages (files appearing in wrong dataset listings, new EFTA designations, new site sections), and
requests for additional metadata on releases and court records.

## What We Can Supply

1. **Parquet and CSV change feeds** (planned for Slice 2): Once Slice 1 completes, the register
   will publish change events as `added`, `removed`, `reuploaded_identical`, `reuploaded_changed`,
   `moved_dataset`. Each event carries observation timestamp, source, document identity (Bates
   number or archive digest), and file URLs. This supports their dashboard and diff tracking.

2. **Archived DOJ observation snapshots** (when available): capture timestamp, source URL,
   listing response status, file counts, and (when available via Wayback) archive digests.
   Supports their preservation and verification work.

3. **Claimed-hash metadata** (yung-megafone/Epstein-Files, future): when the community
   contributes hash lists, the register stores them with source and capture date labels.
   The verifier's goal of comparing versions over time requires independent verification.

4. **API documentation** (Slice 5 and beyond): documented column contract, semver'd schema,
   and a working example of querying the Parquet tables. Lowers their barrier to integration.

## What We Will Not Supply

1. **Document content or full PDFs**: The register does not host or redistribute documents,
   in keeping with D-002 (scope to court-record PDFs only, not media) and D-003 (no mirroring).
   They must source PDFs from DOJ, Wayback, or other archives directly.

2. **Torrent distribution or seeding**: Out of scope. The register records change metadata;
   distribution infrastructure is a separate project.

3. **Recovered redaction content in public tables** (D-004): Findings (page, bbox, character
   count, entity type) are public; recovered text is restricted. The register will not publish
   unredacted content in any form.

4. **Scope outside court-record and disclosure PDFs** (D-002): The media datasets (images,
   video) are excluded; the register covers text-native PDFs only.

## Drafted Comment for Issue #27

To be posted once Slice 1 completes (do not post now):

> We're building a complementary change register for the DOJ Epstein Library
> (github.com/chrfoyer/epstein-change-register). Once our Slice 1 classifier is complete,
> we'll be publishing weekly Parquet + CSV feeds of change events (`added`, `removed`,
> `reuploaded_identical`, `reuploaded_changed`, `moved_dataset`) with full observation
> metadata — source, timestamps, document identity (Bates number or archive digest), and
> file URLs.
>
> If useful for your diff tracker, we can make those feeds available on a stable URL as a
> machine-readable alternative to your dashboard's HTML scraping. We'll also link your
> visual tracker in our register as a complementary resource. Your work tracking upstream
> inconsistencies (#24, #28, #30) is exactly the signal we need.

## Next Steps

- Once Slice 1 completes, post the drafted comment on issue #27 offering the Parquet + CSV feeds.
- Link this register to the yung-megafone/Epstein-Files README as a complementary data source.
- Stay responsive to upstream inconsistencies they report and incorporate observations into
  the register's model.
