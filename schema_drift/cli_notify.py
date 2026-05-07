"""CLI sub-commands for drift notifications."""
from __future__ import annotations

import argparse
import sys

from schema_drift.comparator import compare_snapshots
from schema_drift.notifier import NotificationConfig, build_notification
from schema_drift.storage import load_snapshot


def cmd_notify(args: argparse.Namespace) -> int:
    """Compare two snapshots and print a notification if drift is found.

    Exit codes:
        0 — no drift (or drift below threshold)
        1 — drift detected
        2 — error
    """
    try:
        snap_from = load_snapshot(args.storage_dir, args.from_id)
    except FileNotFoundError:
        print(f"error: snapshot '{args.from_id}' not found", file=sys.stderr)
        return 2

    try:
        snap_to = load_snapshot(args.storage_dir, args.to_id)
    except FileNotFoundError:
        print(f"error: snapshot '{args.to_id}' not found", file=sys.stderr)
        return 2

    cfg = NotificationConfig(
        min_severity=args.min_severity,
        include_tables=args.include_tables or [],
        exclude_tables=args.exclude_tables or [],
    )

    result = compare_snapshots(snap_from, snap_to)
    notification = build_notification(result, cfg)

    if notification is None:
        print("No significant schema drift detected.")
        return 0

    print(notification.as_text())
    return 1


def register_notify_commands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("notify", help="Report schema drift as a notification")
    p.add_argument("from_id", help="Source snapshot ID")
    p.add_argument("to_id", help="Target snapshot ID")
    p.add_argument(
        "--storage-dir",
        default=".schema_drift",
        dest="storage_dir",
        help="Directory where snapshots are stored",
    )
    p.add_argument(
        "--min-severity",
        default="info",
        choices=["info", "warning", "critical"],
        dest="min_severity",
        help="Minimum severity level to include in the notification",
    )
    p.add_argument(
        "--include-tables",
        nargs="*",
        dest="include_tables",
        metavar="TABLE",
        help="Only report drift for these tables",
    )
    p.add_argument(
        "--exclude-tables",
        nargs="*",
        dest="exclude_tables",
        metavar="TABLE",
        help="Skip drift reporting for these tables",
    )
    p.set_defaults(func=cmd_notify)
