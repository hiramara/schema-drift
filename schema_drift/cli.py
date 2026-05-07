"""Command-line interface for schema-drift."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schema_drift.changelog import changelog_to_dict, generate_changelog
from schema_drift.differ import diff_tables
from schema_drift.storage import (
    DEFAULT_SNAPSHOT_DIR,
    latest_snapshot,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


def cmd_list(args: argparse.Namespace) -> int:
    ids = list_snapshots(args.dir)
    if not ids:
        print("No snapshots found.")
    else:
        for sid in ids:
            print(sid)
    return 0


def cmd_save(args: argparse.Namespace) -> int:
    from schema_drift.snapshot import from_dict

    raw = json.loads(Path(args.file).read_text(encoding="utf-8"))
    snapshot = from_dict(raw)
    path = save_snapshot(snapshot, directory=args.dir)
    print(f"Snapshot '{snapshot.snapshot_id}' saved to {path}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    if args.before:
        before = load_snapshot(args.before, directory=args.dir)
    else:
        before = latest_snapshot(directory=args.dir)
        if before is None:
            print("No previous snapshot found.", file=sys.stderr)
            return 1

    after = load_snapshot(args.after, directory=args.dir)
    changes = diff_tables(before, after)
    changelog = generate_changelog(before, after, changes)

    if args.json:
        print(json.dumps(changelog_to_dict(before, after, changes), indent=2))
    else:
        print(changelog)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schema-drift",
        description="Detect and report schema changes in databases over time.",
    )
    parser.add_argument("--dir", default=DEFAULT_SNAPSHOT_DIR, help="Snapshot storage directory")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List stored snapshots")

    p_save = sub.add_parser("save", help="Save a snapshot from a JSON file")
    p_save.add_argument("file", help="Path to snapshot JSON file")

    p_diff = sub.add_parser("diff", help="Show changelog between two snapshots")
    p_diff.add_argument("after", help="ID of the newer snapshot")
    p_diff.add_argument("--before", default=None, help="ID of the older snapshot (default: latest)")
    p_diff.add_argument("--json", action="store_true", help="Output changelog as JSON")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {"list": cmd_list, "save": cmd_save, "diff": cmd_diff}
    return dispatch[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
