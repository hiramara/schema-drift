"""CLI command: summarize drift between two snapshots."""

from __future__ import annotations

import argparse
import json
import sys

from schema_drift.storage import load_snapshot
from schema_drift.comparator import compare_snapshots
from schema_drift.summarizer import summarize


def cmd_summarize(args: argparse.Namespace) -> int:
    from_snap = load_snapshot(args.storage_dir, args.from_id)
    if from_snap is None:
        print(f"Error: snapshot '{args.from_id}' not found.", file=sys.stderr)
        return 2

    to_snap = load_snapshot(args.storage_dir, args.to_id)
    if to_snap is None:
        print(f"Error: snapshot '{args.to_id}' not found.", file=sys.stderr)
        return 2

    result = compare_snapshots(from_snap, to_snap)
    summary = summarize(result)

    if args.json:
        print(json.dumps(summary.to_dict(), indent=2))
        return 0

    print(f"Drift Summary: {summary.from_id} → {summary.to_id}")
    print(f"  Total changes : {summary.total_changes}")
    print(f"  Critical       : {summary.critical_count}")
    print(f"  Warning        : {summary.warning_count}")
    print(f"  Info           : {summary.info_count}")

    if summary.by_table:
        print("\n  Changes by table:")
        for table, count in sorted(summary.by_table.items()):
            print(f"    {table}: {count}")

    if summary.by_type:
        print("\n  Changes by type:")
        for change_type, count in sorted(summary.by_type.items()):
            print(f"    {change_type}: {count}")

    return 0


def register_summarize_commands(
    subparsers: argparse._SubParsersAction,
    common: argparse.ArgumentParser,
) -> None:
    p = subparsers.add_parser(
        "summarize",
        parents=[common],
        help="Print a statistical summary of schema drift between two snapshots.",
    )
    p.add_argument("from_id", help="ID of the earlier snapshot.")
    p.add_argument("to_id", help="ID of the later snapshot.")
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output summary as JSON.",
    )
    p.set_defaults(func=cmd_summarize)
