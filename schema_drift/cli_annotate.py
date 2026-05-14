"""CLI sub-commands for managing snapshot annotations."""
from __future__ import annotations

import argparse
import sys

from schema_drift import annotator


def cmd_annotation_add(args: argparse.Namespace) -> int:
    """Add a note to a snapshot."""
    annotator.add_annotation(args.storage, args.snapshot_id, args.note)
    print(f"Note added to '{args.snapshot_id}'.")
    return 0


def cmd_annotation_remove(args: argparse.Namespace) -> int:
    """Remove a note from a snapshot."""
    removed = annotator.remove_annotation(args.storage, args.snapshot_id, args.note)
    if not removed:
        print(f"Note not found on '{args.snapshot_id}'.", file=sys.stderr)
        return 1
    print(f"Note removed from '{args.snapshot_id}'.")
    return 0


def cmd_annotation_list(args: argparse.Namespace) -> int:
    """List all notes for a snapshot."""
    notes = annotator.get_annotations(args.storage, args.snapshot_id)
    if not notes:
        print(f"No annotations for '{args.snapshot_id}'.")
    else:
        for note in notes:
            print(f"  - {note}")
    return 0


def cmd_annotation_clear(args: argparse.Namespace) -> int:
    """Clear annotations (one snapshot or all)."""
    sid = getattr(args, "snapshot_id", None)
    annotator.clear_annotations(args.storage, sid)
    target = f"'{sid}'" if sid else "all snapshots"
    print(f"Annotations cleared for {target}.")
    return 0


def register_annotation_commands(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
) -> None:
    # add
    p_add = subparsers.add_parser("annotation-add", help="Add a note to a snapshot")
    p_add.add_argument("snapshot_id")
    p_add.add_argument("note")
    p_add.set_defaults(func=cmd_annotation_add)

    # remove
    p_rm = subparsers.add_parser("annotation-remove", help="Remove a note from a snapshot")
    p_rm.add_argument("snapshot_id")
    p_rm.add_argument("note")
    p_rm.set_defaults(func=cmd_annotation_remove)

    # list
    p_ls = subparsers.add_parser("annotation-list", help="List notes for a snapshot")
    p_ls.add_argument("snapshot_id")
    p_ls.set_defaults(func=cmd_annotation_list)

    # clear
    p_cl = subparsers.add_parser("annotation-clear", help="Clear annotations")
    p_cl.add_argument("snapshot_id", nargs="?", default=None)
    p_cl.set_defaults(func=cmd_annotation_clear)
