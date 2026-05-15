"""CLI commands for the schema change timeline feature."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from schema_drift.storage import load_snapshot
from schema_drift.differ_timeline import build_timeline


def cmd_timeline(args: argparse.Namespace) -> int:
    """Print a timeline of schema changes across a series of snapshot IDs."""
    snapshots = []
    for snap_id in args.snapshot_ids:
        snap = load_snapshot(args.storage_dir, snap_id)
        if snap is None:
            print(f"Error: snapshot '{snap_id}' not found.", file=sys.stderr)
            return 2
        snapshots.append(snap)

    if len(snapshots) < 2:
        print("Error: provide at least two snapshot IDs.", file=sys.stderr)
        return 2

    try:
        timeline = build_timeline(snapshots)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(timeline.to_dict(), indent=2))
        return 0

    # Human-readable summary
    print(f"Timeline across {len(timeline.snapshot_ids)} snapshots")
    print(f"Total changes : {timeline.total_changes}")
    print()
    for entry in timeline.entries:
        print(f"  {entry.from_id}  →  {entry.to_id}  ({len(entry.changes)} change(s))")
        for change in entry.changes:
            symbol = "+" if "added" in change.change_type.value else "-"
            col_info = f" [{change.column}]" if change.column else ""
            print(f"    {symbol} [{change.change_type.value}] {change.table}{col_info}")

    return 0


def register_timeline_commands(
    subparsers: argparse._SubParsersAction,
    storage_dir: str,
) -> None:
    """Register the 'timeline' sub-command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "timeline",
        help="Show schema change timeline across multiple snapshots.",
    )
    parser.add_argument(
        "snapshot_ids",
        nargs="+",
        metavar="SNAPSHOT_ID",
        help="Two or more snapshot IDs in chronological order.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.set_defaults(func=cmd_timeline, storage_dir=storage_dir)
