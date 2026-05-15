"""CLI commands for tracing a table or column history."""

from __future__ import annotations

import argparse
import json
import sys

from schema_drift.storage import load_snapshot
from schema_drift.tracer import trace_column, trace_table


def cmd_trace(args: argparse.Namespace) -> int:
    snapshots = []
    for sid in args.snapshot_ids:
        snap = load_snapshot(args.storage_dir, sid)
        if snap is None:
            print(f"Snapshot not found: {sid}", file=sys.stderr)
            return 2
        snapshots.append(snap)

    if not snapshots:
        print("No snapshots provided.", file=sys.stderr)
        return 2

    if args.column:
        result = trace_column(snapshots, args.table, args.column)
    else:
        result = trace_table(snapshots, args.table)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        col_label = f".{args.column}" if args.column else ""
        print(f"Trace: {args.table}{col_label}")
        print(f"{'Snapshot':<36}  {'Exists':<6}  Detail")
        print("-" * 60)
        for entry in result.entries:
            detail_str = ", ".join(f"{k}={v}" for k, v in entry.detail.items())
            print(f"{entry.snapshot_id:<36}  {str(entry.exists):<6}  {detail_str}")
    return 0


def register_trace_commands(
    subparsers: argparse._SubParsersAction,
    storage_dir: str,
) -> None:
    p = subparsers.add_parser("trace", help="Trace a table or column across snapshots")
    p.add_argument("table", help="Table name to trace")
    p.add_argument("--column", default=None, help="Column name to trace within table")
    p.add_argument(
        "snapshot_ids",
        nargs="+",
        metavar="SNAPSHOT_ID",
        help="Ordered list of snapshot IDs to trace across",
    )
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_trace, storage_dir=storage_dir)
