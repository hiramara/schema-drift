"""CLI sub-commands for the comparator feature."""

from __future__ import annotations

import argparse
import json
import sys

from .changelog import generate_changelog
from .comparator import compare_latest_two, compare_snapshots
from .storage import load_snapshot


def _load_snapshot_pair(storage_dir: str, old_id: str, new_id: str, err):
    """Load a pair of snapshots by ID, writing errors to *err*.

    Returns ``(old, new)`` on success or ``None`` if either snapshot cannot
    be found.
    """
    try:
        old = load_snapshot(storage_dir, old_id)
    except FileNotFoundError as exc:
        err.write(f"Error: {exc}\n")
        return None
    try:
        new = load_snapshot(storage_dir, new_id)
    except FileNotFoundError as exc:
        err.write(f"Error: {exc}\n")
        return None
    return old, new


def cmd_compare(
    args: argparse.Namespace,
    out=sys.stdout,
    err=sys.stderr,
) -> int:
    """Compare two snapshots by ID (or the latest two when IDs are omitted)."""
    storage_dir: str = args.storage_dir

    if args.old_id and args.new_id:
        pair = _load_snapshot_pair(storage_dir, args.old_id, args.new_id, err)
        if pair is None:
            return 1
        old, new = pair
        result = compare_snapshots(old, new)
    else:
        result = compare_latest_two(storage_dir)
        if result is None:
            err.write("Error: need at least two snapshots to compare.\n")
            return 1

    fmt: str = getattr(args, "format", "text")

    if fmt == "json":
        json.dump(result.to_dict(), out, indent=2)
        out.write("\n")
    else:
        lines = generate_changelog(
            result.old_snapshot,
            result.new_snapshot,
            result.changes,
        )
        out.write("\n".join(lines) + "\n")

    return 0


def register_compare_commands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach the *compare* sub-command to an existing subparsers group."""
    p = subparsers.add_parser(
        "compare",
        help="compare two snapshots and show a changelog",
    )
    p.add_argument(
        "--old-id",
        dest="old_id",
        default=None,
        help="ID of the older snapshot (defaults to second-latest)",
    )
    p.add_argument(
        "--new-id",
        dest="new_id",
        default=None,
        help="ID of the newer snapshot (defaults to latest)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="output format (default: text)",
    )
    p.set_defaults(func=cmd_compare)
