"""Deterministic change-event classifier. Converts observations into change events."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ChangeEvent:
    """A single change event. Hashable for deduplication."""
    capture_ts: str
    source_url: str
    event_type: str  # added | removed | reuploaded_identical | reuploaded_changed | moved_dataset
    source_name: str  # analytics | wayback
    file_url: str
    bates_id: Optional[str]
    dataset: str
    prior_dataset: Optional[str]
    archive_digest: Optional[str]
    prior_archive_digest: Optional[str]
    archive_url: Optional[str]
    archive_ts: Optional[str]
    notes: Optional[str] = None

    def to_dict(self):
        """Convert to dict for database insertion."""
        return {
            "capture_ts": self.capture_ts,
            "source_url": self.source_url,
            "event_type": self.event_type,
            "source_name": self.source_name,
            "file_url": self.file_url,
            "bates_id": self.bates_id,
            "dataset": self.dataset,
            "prior_dataset": self.prior_dataset,
            "archive_digest": self.archive_digest,
            "prior_archive_digest": self.prior_archive_digest,
            "archive_url": self.archive_url,
            "archive_ts": self.archive_ts,
            "notes": self.notes,
        }


def _get_identity_key(bates_id: Optional[str], archive_digest: Optional[str]) -> Optional[str]:
    """
    Get the identity key for a file.

    Bates ID takes precedence if present (D-013).
    Falls back to archive_digest if no bates_id.
    Returns None if both are missing (unknown identity).
    """
    if bates_id:
        return bates_id
    if archive_digest:
        return archive_digest
    return None


def classify_listings(listings_and_files: list[dict], complete_by_source: dict[str, bool] | None = None) -> list[ChangeEvent]:
    """
    Classify change events from a sequence of listing captures and their files.

    Input: list of dicts with keys:
        listing: {run_id, capture_ts, source_url, listing_url, archive_url, archive_ts, status, row_count}
        files: [
            {run_id, capture_ts, source_url, listing_url, file_url, bates_id, dataset, archive_digest},
            ...
        ]

    Args:
        listings_and_files: sequence of polls with files
        complete_by_source: dict mapping source_url -> bool indicating if listing is complete (all pages, etc.).
                           If source not in dict, defaults to False (incomplete). None values mean unknown.

    Processed in capture_ts order. Removal requires two consecutive "ok" polls (both explicitly complete)
    with absence plus archive_url/archive_ts (archive proof, D-007). Returns list of ChangeEvent objects.
    """
    if not listings_and_files:
        return []

    if complete_by_source is None:
        complete_by_source = {}

    events = []
    # Maps: identity_key -> list of (capture_ts, file_record or None)
    # where identity_key is either bates_id (preferred) or archive_digest
    file_history: dict[str, list[tuple[str, dict | None]]] = {}
    # Track prior poll's contents and completeness to detect removals
    prior_poll_ids: set[str] | None = None
    prior_poll_complete: bool = False
    prior_poll_source: str | None = None

    for item in listings_and_files:
        listing = item.get("listing", {})
        files = item.get("files", [])
        capture_ts = listing.get("capture_ts")
        status = listing.get("status", "ok")
        archive_url = listing.get("archive_url")
        archive_ts = listing.get("archive_ts")
        source_url = listing.get("source_url")

        if status != "ok":
            # error | blocked | empty listings emit nothing (D-007), don't trigger removal
            prior_poll_ids = None  # Reset so next ok poll doesn't trigger removal
            prior_poll_complete = False
            prior_poll_source = None
            continue

        # Check if this poll is marked complete (default: incomplete)
        current_poll_complete = complete_by_source.get(source_url, False)

        # Build identity->file map for this poll
        current_files: dict[str, dict] = {}
        for f in files:
            bates_id = f.get("bates_id")
            archive_digest = f.get("archive_digest")
            identity_key = _get_identity_key(bates_id, archive_digest)
            if identity_key:
                current_files[identity_key] = f

        current_ids = set(current_files.keys())

        # Initialize history for any new identities
        for identity_key in current_ids:
            if identity_key not in file_history:
                file_history[identity_key] = []

        # Process each file in current poll
        for identity_key, current_file in current_files.items():
            bates_id = current_file.get("bates_id")
            archive_digest = current_file.get("archive_digest")

            # Get prior record for this identity
            if identity_key in file_history and file_history[identity_key]:
                prior_ts, prior_file = file_history[identity_key][-1]
            else:
                prior_ts, prior_file = None, None

            file_history[identity_key].append((capture_ts, current_file))

            # Unknown identity (no bates_id and no digest): emit added only on first observation
            if not bates_id and not archive_digest:
                continue

            if prior_file is None:
                # First observation of this identity -> added
                events.append(
                    ChangeEvent(
                        capture_ts=capture_ts,
                        source_url=source_url,
                        event_type="added",
                        source_name="wayback",
                        file_url=current_file.get("file_url"),
                        bates_id=bates_id,
                        dataset=current_file.get("dataset"),
                        prior_dataset=None,
                        archive_digest=archive_digest,
                        prior_archive_digest=None,
                        archive_url=archive_url,
                        archive_ts=archive_ts,
                    )
                )
            else:
                # File was present before, still present. Check for changes.
                prior_digest = prior_file.get("archive_digest")
                is_dataset_move = current_file.get("dataset") != prior_file.get("dataset")

                # Check for content change (reuploaded_changed)
                # Only if both digests present and they differ; cannot classify if digest is NULL (D-011)
                if (
                    archive_digest is not None
                    and prior_digest is not None
                    and archive_digest != prior_digest
                ):
                    events.append(
                        ChangeEvent(
                            capture_ts=capture_ts,
                            source_url=source_url,
                            event_type="reuploaded_changed",
                            source_name="wayback",
                            file_url=current_file.get("file_url"),
                            bates_id=bates_id,
                            dataset=current_file.get("dataset"),
                            prior_dataset=prior_file.get("dataset"),
                            archive_digest=archive_digest,
                            prior_archive_digest=prior_digest,
                            archive_url=archive_url,
                            archive_ts=archive_ts,
                        )
                    )

                # Check for dataset move (takes precedence over URL change)
                if is_dataset_move:
                    events.append(
                        ChangeEvent(
                            capture_ts=capture_ts,
                            source_url=source_url,
                            event_type="moved_dataset",
                            source_name="wayback",
                            file_url=current_file.get("file_url"),
                            bates_id=bates_id,
                            dataset=current_file.get("dataset"),
                            prior_dataset=prior_file.get("dataset"),
                            archive_digest=archive_digest,
                            prior_archive_digest=None,
                            archive_url=archive_url,
                            archive_ts=archive_ts,
                        )
                    )
                # Check for URL change (reuploaded_identical)
                # Only if same dataset, both digests present and equal, but different URL
                # Cannot claim identical if digest is NULL in either poll (D-011 unknown identity)
                elif (
                    archive_digest is not None
                    and prior_digest is not None
                    and current_file.get("file_url") != prior_file.get("file_url")
                    and archive_digest == prior_digest
                ):
                    events.append(
                        ChangeEvent(
                            capture_ts=capture_ts,
                            source_url=source_url,
                            event_type="reuploaded_identical",
                            source_name="wayback",
                            file_url=current_file.get("file_url"),
                            bates_id=bates_id,
                            dataset=current_file.get("dataset"),
                            prior_dataset=prior_file.get("dataset"),
                            archive_digest=archive_digest,
                            prior_archive_digest=None,
                            archive_url=archive_url,
                            archive_ts=archive_ts,
                        )
                    )

        # Check for removals: file was present before, absent in prior poll AND absent now (D-007)
        # Removal also requires BOTH consecutive polls to be marked complete (D-013)
        if prior_poll_ids is not None and prior_poll_complete and current_poll_complete:
            # We have two consecutive complete ok polls to compare against
            for identity_key in file_history:
                if identity_key not in current_ids and identity_key not in prior_poll_ids:
                    # File is absent in both prior and current polls, and both are complete
                    # Get the last known state before absence
                    last_known = None
                    for ts, rec in reversed(file_history[identity_key]):
                        if rec is not None:
                            last_known = rec
                            break

                    if last_known:
                        bates_id = last_known.get("bates_id")
                        archive_digest = last_known.get("archive_digest")

                        # Only emit removal if we have identity and archive proof (D-007)
                        if (bates_id or archive_digest) and archive_url and archive_ts:
                            events.append(
                                ChangeEvent(
                                    capture_ts=capture_ts,
                                    source_url=source_url,
                                    event_type="removed",
                                    source_name="wayback",
                                    file_url=last_known.get("file_url"),
                                    bates_id=bates_id,
                                    dataset=last_known.get("dataset"),
                                    prior_dataset=None,
                                    archive_digest=archive_digest,
                                    prior_archive_digest=None,
                                    archive_url=archive_url,
                                    archive_ts=archive_ts,
                                )
                            )

        # Record absences for files that were in history but not in current poll
        for identity_key in file_history:
            if identity_key not in current_files:
                file_history[identity_key].append((capture_ts, None))

        # Update prior poll info for next iteration
        prior_poll_ids = current_ids
        prior_poll_complete = current_poll_complete
        prior_poll_source = source_url

    return events
