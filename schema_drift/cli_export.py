"""CLI sub-commands for exporting snapshots and diffs."""

from __future__ import annotations

import argparse
import sys

from schema_drift.differ import diff_tables
from schema_drift.exporter import EXPORT_FORMATS, export_diff, export_snapshot_json
from schema_drift.storage import load_snapshot


def cmd_export_snapshot(args: argparse.Namespace) -> None:
    """Export a single snapshot to JSON and print to stdout."""
    try:
        snapshot = load_snapshot(args.storage_dir, args.snapshot_id)
    except FileNotFoundError:
        print(f"Error: snapshot '{args.snapshot_id}' not found.", file=sys.stderr)
        sys.exit(1)

    output = export_snapshot_json(snapshot, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"Snapshot exported to {args.output}")
    else:
        print(output)


def cmd_export_diff(args: argparse.Namespace) -> None:
    """Export a diff between two snapshots in the requested format."""
    try:
        old = load_snapshot(args.storage_dir, args.old_id)
    except FileNotFoundError:
        print(f"Error: snapshot '{args.old_id}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        new = load_snapshot(args.storage_dir, args.new_id)
    except FileNotFoundError:
        print(f"Error: snapshot '{args.new_id}' not found.", file=sys.stderr)
        sys.exit(1)

    changes = diff_tables(old.tables, new.tables)
    output = export_diff(old, new, changes, fmt=args.format)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"Diff exported to {args.output}")
    else:
        print(output)


def register_export_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach export sub-commands to an existing subparsers group."""
    # export-snapshot
    p_snap = subparsers.add_parser(
        "export-snapshot",
        help="Export a snapshot to JSON",
    )
    p_snap.add_argument("snapshot_id", help="ID of the snapshot to export")
    p_snap.add_argument("--storage-dir", default=".schema_drift", dest="storage_dir")
    p_snap.add_argument("--output", "-o", default=None, help="Write to file instead of stdout")
    p_snap.set_defaults(func=cmd_export_snapshot)

    # export-diff
    p_diff = subparsers.add_parser(
        "export-diff",
        help="Export a diff between two snapshots",
    )
    p_diff.add_argument("old_id", help="ID of the older snapshot")
    p_diff.add_argument("new_id", help="ID of the newer snapshot")
    p_diff.add_argument(
        "--format",
        "-f",
        choices=sorted(EXPORT_FORMATS),
        default="json",
        help="Output format (default: json)",
    )
    p_diff.add_argument("--storage-dir", default=".schema_drift", dest="storage_dir")
    p_diff.add_argument("--output", "-o", default=None, help="Write to file instead of stdout")
    p_diff.set_defaults(func=cmd_export_diff)
