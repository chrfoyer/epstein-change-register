"""Command-line interface for the change register."""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb

from register.classifier import classify_listings
from register.store import connect


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Epstein Library change register reporting."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # report command
    report_parser = subparsers.add_parser("report", help="Report changes")
    report_parser.add_argument(
        "--since",
        type=str,
        default="7d",
        help="Time period for changes (e.g., 7d, 30d, 1h)",
    )
    report_parser.add_argument(
        "--db",
        type=str,
        default=":memory:",
        help="Database path (default: in-memory)",
    )
    report_parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json", "csv"],
        default="text",
        help="Output format",
    )

    return parser.parse_args()


def parse_time_delta(since_str: str) -> timedelta:
    """Parse a time delta string like '7d', '30d', '1h', '24h'."""
    if since_str.endswith("d"):
        days = int(since_str[:-1])
        return timedelta(days=days)
    elif since_str.endswith("h"):
        hours = int(since_str[:-1])
        return timedelta(hours=hours)
    else:
        raise ValueError(f"Unsupported time delta format: {since_str}")


def get_change_events(con: duckdb.DuckDBPyConnection, since: timedelta) -> list[dict]:
    """Fetch change events from the database for the given time period."""
    cutoff_ts = (datetime.now(timezone.utc) - since).isoformat()

    result = con.execute(
        """
        SELECT
            capture_ts,
            source_url,
            event_type,
            source_name,
            file_url,
            bates_id,
            dataset,
            prior_dataset,
            archive_digest,
            prior_archive_digest,
            archive_url,
            archive_ts,
            notes
        FROM change_event
        WHERE capture_ts >= ?
        ORDER BY capture_ts DESC, event_type
        """,
        [cutoff_ts],
    )

    return result.fetchall()


def format_text_report(events: list) -> str:
    """Format events as plain text."""
    if not events:
        return "No changes in the specified period.\n"

    lines = [f"Changes (last {len(events)} event{'s' if len(events) != 1 else ''}):\n"]

    event_types = {}
    for event in events:
        etype = event[2]  # event_type
        event_types[etype] = event_types.get(etype, 0) + 1

    for etype, count in sorted(event_types.items()):
        lines.append(f"  {etype}: {count}")

    lines.append("")

    for event in events:
        capture_ts, source_url, event_type, source_name, file_url, bates_id, dataset, prior_dataset, archive_digest, prior_archive_digest, archive_url, archive_ts, notes = event

        bates_part = f" ({bates_id})" if bates_id else ""
        dataset_part = ""
        if prior_dataset and prior_dataset != dataset:
            dataset_part = f" {prior_dataset} → {dataset}"
        elif dataset:
            dataset_part = f" {dataset}"

        short_url = file_url.split("/")[-1] if file_url else "unknown"

        lines.append(f"{capture_ts[:10]} | {event_type:20s} | {short_url:30s}{bates_part}{dataset_part}")

    return "\n".join(lines) + "\n"


def format_json_report(events: list) -> str:
    """Format events as JSON."""
    import json

    result = []
    for event in events:
        result.append({
            "capture_ts": event[0],
            "source_url": event[1],
            "event_type": event[2],
            "source_name": event[3],
            "file_url": event[4],
            "bates_id": event[5],
            "dataset": event[6],
            "prior_dataset": event[7],
            "archive_digest": event[8],
            "prior_archive_digest": event[9],
            "archive_url": event[10],
            "archive_ts": event[11],
            "notes": event[12],
        })

    return json.dumps(result, indent=2)


def format_csv_report(events: list) -> str:
    """Format events as CSV."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "capture_ts", "source_url", "event_type", "source_name", "file_url",
        "bates_id", "dataset", "prior_dataset", "archive_digest",
        "prior_archive_digest", "archive_url", "archive_ts", "notes"
    ])

    for event in events:
        writer.writerow(event)

    return output.getvalue()


def main():
    """Main entry point."""
    args = parse_args()

    if args.command == "report":
        con = connect(args.db)
        since = parse_time_delta(args.since)
        events = get_change_events(con, since)

        if args.format == "json":
            output = format_json_report(events)
        elif args.format == "csv":
            output = format_csv_report(events)
        else:
            output = format_text_report(events)

        print(output, end="")
    else:
        print("No command specified. Use --help for usage.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
