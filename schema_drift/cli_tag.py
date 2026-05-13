"""CLI sub-commands for snapshot tagging."""

from __future__ import annotations

import argparse
import sys

from schema_drift import tagger


def cmd_tag_add(args: argparse.Namespace) -> int:
    tagger.add_tag(args.storage_dir, args.snapshot_id, args.tag)
    print(f"Tag '{args.tag}' added to snapshot '{args.snapshot_id}'.")
    return 0


def cmd_tag_remove(args: argparse.Namespace) -> int:
    removed = tagger.remove_tag(args.storage_dir, args.snapshot_id, args.tag)
    if removed:
        print(f"Tag '{args.tag}' removed from snapshot '{args.snapshot_id}'.")
        return 0
    print(
        f"Tag '{args.tag}' not found on snapshot '{args.snapshot_id}'.",
        file=sys.stderr,
    )
    return 1


def cmd_tag_list(args: argparse.Namespace) -> int:
    tags = tagger.get_tags(args.storage_dir, args.snapshot_id)
    if tags:
        for t in tags:
            print(t)
    else:
        print(f"No tags for snapshot '{args.snapshot_id}'.")
    return 0


def cmd_tag_find(args: argparse.Namespace) -> int:
    ids = tagger.find_by_tag(args.storage_dir, args.tag)
    if ids:
        for sid in ids:
            print(sid)
    else:
        print(f"No snapshots found with tag '{args.tag}'.")
    return 0


def register_tag_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # tag add
    p_add = subparsers.add_parser("tag-add", help="Add a tag to a snapshot")
    p_add.add_argument("snapshot_id")
    p_add.add_argument("tag")
    p_add.set_defaults(func=cmd_tag_add)

    # tag remove
    p_rm = subparsers.add_parser("tag-remove", help="Remove a tag from a snapshot")
    p_rm.add_argument("snapshot_id")
    p_rm.add_argument("tag")
    p_rm.set_defaults(func=cmd_tag_remove)

    # tag list
    p_ls = subparsers.add_parser("tag-list", help="List tags for a snapshot")
    p_ls.add_argument("snapshot_id")
    p_ls.set_defaults(func=cmd_tag_list)

    # tag find
    p_find = subparsers.add_parser("tag-find", help="Find snapshots by tag")
    p_find.add_argument("tag")
    p_find.set_defaults(func=cmd_tag_find)
