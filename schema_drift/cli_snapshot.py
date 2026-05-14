"""cli_snapshot.py — CLI commands for capturing live database snapshots."""

from __future__ import annotations

import argparse
import sys

from schema_drift.snapshotter import capture_snapshot
from schema_drift.storage import save_snapshot


def cmd_capture(args: argparse.Namespace) -> int:
    """Capture a schema snapshot from a live database and persist it."""
    tables = (
        [t.strip() for t in args.tables.split(",") if t.strip()]
        if args.tables
        else None
    )

    try:
        snapshot = capture_snapshot(
            dsn=args.dsn,
            snapshot_id=args.id,
            tables=tables,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: failed to capture snapshot — {exc}", file=sys.stderr)
        return 1

    save_snapshot(args.storage_dir, snapshot)
    table_count = len(snapshot.tables)
    print(
        f"Captured snapshot '{snapshot.snapshot_id}' "
        f"({table_count} table{'s' if table_count != 1 else ''}) "
        f"→ {args.storage_dir}"
    )
    return 0


def register_snapshot_commands(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
) -> None:
    """Attach the *capture* sub-command to *subparsers*."""
    p = subparsers.add_parser(
        "capture",
        help="Capture a live database schema snapshot",
    )
    p.add_argument("dsn", help="SQLAlchemy connection string, e.g. sqlite:///mydb.sqlite3")
    p.add_argument("id", help="Unique snapshot identifier")
    p.add_argument(
        "--tables",
        default=None,
        metavar="TABLE,...",
        help="Comma-separated list of tables to include (default: all)",
    )
    p.add_argument(
        "--storage-dir",
        default=".schema_drift",
        metavar="DIR",
        help="Directory where snapshots are stored (default: .schema_drift)",
    )
    p.set_defaults(func=cmd_capture)
