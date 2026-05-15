"""CLI sub-commands for drift statistics."""
from __future__ import annotations

import argparse
import json
import sys

from schema_drift.storage import load_snapshot
from schema_drift.differ import diff_tables
from schema_drift.differ_stats import compute_diff_stats


def cmd_stats(args: argparse.Namespace) -> int:
    """Print diff statistics between two snapshots."""
    snap_from = load_snapshot(args.storage_dir, args.from_id)
    if snap_from is None:
        print(f"Snapshot not found: {args.from_id}", file=sys.stderr)
        return 2

    snap_to = load_snapshot(args.storage_dir, args.to_id)
    if snap_to is None:
        print(f"Snapshot not found: {args.to_id}", file=sys.stderr)
        return 2

    changes = diff_tables(snap_from, snap_to)
    stats = compute_diff_stats(changes)

    if args.json:
        print(json.dumps(stats.to_dict(), indent=2))
    else:
        print(f"Total changes : {stats.total}")
        print(f"Tables affected: {stats.tables_affected}")
        if stats.by_type:
            print("By type:")
            for k, v in sorted(stats.by_type.items()):
                print(f"  {k}: {v}")
        if stats.by_table:
            print("By table:")
            for k, v in sorted(stats.by_table.items()):
                print(f"  {k}: {v}")
    return 0


def register_stats_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("stats", help="Show diff statistics between two snapshots")
    p.add_argument("from_id", help="Source snapshot ID")
    p.add_argument("to_id", help="Target snapshot ID")
    p.add_argument("--storage-dir", default=".schema_drift", dest="storage_dir")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_stats)
