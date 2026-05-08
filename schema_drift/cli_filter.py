"""CLI sub-commands for filtering diff output."""

from __future__ import annotations

import argparse
import json
import sys

from .storage import load_snapshot
from .differ import diff_tables
from .filter import FilterConfig, apply_filter
from .changelog import generate_changelog


def cmd_filter_diff(args: argparse.Namespace) -> int:
    from_snap = load_snapshot(args.storage_dir, args.from_id)
    if from_snap is None:
        print(f"Snapshot not found: {args.from_id}", file=sys.stderr)
        return 2

    to_snap = load_snapshot(args.storage_dir, args.to_id)
    if to_snap is None:
        print(f"Snapshot not found: {args.to_id}", file=sys.stderr)
        return 2

    all_changes = diff_tables(from_snap, to_snap)

    cfg_data: dict = {}
    if args.tables:
        cfg_data["tables"] = args.tables
    if args.exclude_tables:
        cfg_data["exclude_tables"] = args.exclude_tables
    if args.change_types:
        cfg_data["change_types"] = args.change_types
    if args.min_severity:
        cfg_data["min_severity"] = args.min_severity

    cfg = FilterConfig.from_dict(cfg_data)
    filtered = apply_filter(all_changes, cfg)

    if args.format == "json":
        print(json.dumps([c.to_dict() for c in filtered], indent=2))
    else:
        print(generate_changelog(from_snap, to_snap, filtered))

    return 0


def register_filter_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("filter-diff", help="Diff two snapshots with filtering")
    p.add_argument("from_id", help="Source snapshot ID")
    p.add_argument("to_id", help="Target snapshot ID")
    p.add_argument("--storage-dir", default=".schema_drift", dest="storage_dir")
    p.add_argument(
        "--tables", nargs="+", metavar="TABLE",
        help="Include only these tables",
    )
    p.add_argument(
        "--exclude-tables", nargs="+", metavar="TABLE", dest="exclude_tables",
        help="Exclude these tables",
    )
    p.add_argument(
        "--change-types", nargs="+", metavar="TYPE", dest="change_types",
        help="Include only these change types (e.g. column_added column_removed)",
    )
    p.add_argument(
        "--min-severity", choices=["low", "medium", "critical"], dest="min_severity",
        help="Minimum severity level to include",
    )
    p.add_argument(
        "--format", choices=["text", "json"], default="text",
        help="Output format",
    )
    p.set_defaults(func=cmd_filter_diff)
