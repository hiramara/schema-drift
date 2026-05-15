"""CLI commands for linting schema snapshots."""

from __future__ import annotations

import json
import sys

from schema_drift.linter import lint_snapshot
from schema_drift.storage import load_snapshot


def cmd_lint(args) -> int:
    """Lint a stored snapshot and report issues."""
    snapshot = load_snapshot(args.storage_dir, args.snapshot_id)
    if snapshot is None:
        print(f"Snapshot '{args.snapshot_id}' not found.", file=sys.stderr)
        return 2

    result = lint_snapshot(snapshot)

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
        return 1 if result.error_count > 0 else 0

    # Default: human-readable text
    if not result.has_issues:
        print(f"No issues found in snapshot '{result.snapshot_id}'.")
        return 0

    print(f"Lint results for snapshot '{result.snapshot_id}':")
    print(f"  Errors:   {result.error_count}")
    print(f"  Warnings: {result.warning_count}")
    print()

    for issue in result.issues:
        location = issue.table
        if issue.column:
            location += f".{issue.column}"
        tag = issue.severity.upper()
        print(f"  [{tag}] {issue.code} @ {location}: {issue.message}")

    return 1 if result.error_count > 0 else 0


def register_lint_commands(subparsers, common_args):
    p = subparsers.add_parser("lint", help="Lint a snapshot for structural issues.")
    common_args(p)
    p.add_argument("snapshot_id", help="ID of the snapshot to lint.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=cmd_lint)
