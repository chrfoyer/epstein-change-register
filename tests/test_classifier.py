"""Tests for the change-event classifier using synthetic fixtures."""

import json
from pathlib import Path

import pytest

from register.classifier import ChangeEvent, classify_listings


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(scenario_name: str) -> tuple[list[dict], list[dict]]:
    """Load a fixture: input data and expected output."""
    input_file = FIXTURES_DIR / f"{scenario_name}.json"
    expected_file = FIXTURES_DIR / f"{scenario_name}_expected.json"

    with open(input_file) as f:
        input_data = json.load(f)

    with open(expected_file) as f:
        expected = json.load(f)

    return input_data, expected


def normalize_event(event: ChangeEvent | dict) -> dict:
    """Normalize a ChangeEvent or dict to a comparable dict."""
    if isinstance(event, ChangeEvent):
        return event.to_dict()
    return event


@pytest.mark.parametrize("scenario", [
    "scenario_1_stable",
    "scenario_2_flaky",
    "scenario_3_removed",
    "scenario_4_reuploaded_identical",
    "scenario_5_reuploaded_changed",
    "scenario_6_moved",
    "scenario_7_error",
    "scenario_8_empty",
])
def test_classifier_scenarios(scenario: str):
    """Test classifier against all scenarios."""
    input_data, expected = load_fixture(scenario)

    events = classify_listings(input_data)
    actual = [normalize_event(e) for e in events]

    # Sort for comparison (order shouldn't matter for correctness)
    actual_sorted = sorted(actual, key=lambda e: (e["capture_ts"], e["event_type"]))
    expected_sorted = sorted(expected, key=lambda e: (e["capture_ts"], e["event_type"]))

    assert len(actual_sorted) == len(expected_sorted), (
        f"Event count mismatch: {len(actual_sorted)} vs {len(expected_sorted)}"
    )

    for i, (actual_event, expected_event) in enumerate(zip(actual_sorted, expected_sorted)):
        assert actual_event == expected_event, (
            f"Event {i} mismatch:\nActual: {actual_event}\nExpected: {expected_event}"
        )


def test_empty_input():
    """Test classifier with empty input."""
    events = classify_listings([])
    assert events == []


def test_single_file_no_events():
    """Test single file with no changes."""
    input_data = [
        {
            "listing": {
                "run_id": "run_1",
                "capture_ts": "2026-10-04T10:00:00+00:00",
                "source_url": "http://archive.org",
                "listing_url": "http://archive.org/DataSet1",
                "archive_url": "http://archive.org",
                "archive_ts": "2026-10-04T10:00:00+00:00",
                "status": "ok",
                "row_count": 1,
            },
            "files": [
                {
                    "run_id": "run_1",
                    "capture_ts": "2026-10-04T10:00:00+00:00",
                    "source_url": "http://archive.org",
                    "listing_url": "http://archive.org/DataSet1",
                    "file_url": "http://justice.gov/DataSet 1/file1.pdf",
                    "bates_id": "EFTA00000001",
                    "dataset": "DataSet 1",
                    "archive_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                }
            ],
        },
        {
            "listing": {
                "run_id": "run_2",
                "capture_ts": "2026-10-05T10:00:00+00:00",
                "source_url": "http://archive.org",
                "listing_url": "http://archive.org/DataSet1",
                "archive_url": "http://archive.org",
                "archive_ts": "2026-10-05T10:00:00+00:00",
                "status": "ok",
                "row_count": 1,
            },
            "files": [
                {
                    "run_id": "run_2",
                    "capture_ts": "2026-10-05T10:00:00+00:00",
                    "source_url": "http://archive.org",
                    "listing_url": "http://archive.org/DataSet1",
                    "file_url": "http://justice.gov/DataSet 1/file1.pdf",
                    "bates_id": "EFTA00000001",
                    "dataset": "DataSet 1",
                    "archive_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                }
            ],
        },
    ]

    events = classify_listings(input_data)

    # Should have exactly one "added" event for the first observation
    assert len(events) == 1
    assert events[0].event_type == "added"
    assert events[0].bates_id == "EFTA00000001"
