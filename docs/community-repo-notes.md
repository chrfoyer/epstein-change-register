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

1. **Parquet and CSV change feeds** (machine-readable): Once Slice 1 completes, the register will
   publish change events weekly: `added`, `removed`, `reuploaded_identical`, `reuploaded_changed`,
   `moved_dataset`. Each event carries observation timestamp, source, document identity (Bates
   number or archive digest), and file URLs. This supports their dashboard and diff tracking.

2. **Archived DOJ observation snapshots** on a published schedule: capture timestamp, source URL,
   listing response status, file counts, and (when available via Wayback) archive digests and
   snapshots. Supports their preservation and verification work.

3. **Claimed-hash metadata** (Source C, future): when the community contributes hash lists,
   the register stores them alongside measured hashes from archive sources, labeled with source
   and capture date. Supports the verifier's goal of comparing versions over time.

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

## Next Steps

- Once Slice 1 completes, post a pointer to the change-event feed on issue #27, offering
  the Parquet + CSV as a machine-readable alternative to their dashboard's HTML scraping.
- Link this register to their README as a complementary data source for change tracking.
- Stay responsive to upstream inconsistencies they report (#24, #28, #30) and incorporate
  observations into the register's model.
