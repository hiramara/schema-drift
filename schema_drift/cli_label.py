"""CLI commands for snapshot labeling."""

from __future__ import annotations

import argparse

from schema_drift import labeler


def cmd_label_set(args: argparse.Namespace) -> int:
    labeler.set_label(args.storage_dir, args.snapshot_id, args.label)
    print(f"Label '{args.label}' set for snapshot '{args.snapshot_id}'.")
    return 0


def cmd_label_remove(args: argparse.Namespace) -> int:
    removed = labeler.remove_label(args.storage_dir, args.snapshot_id)
    if removed:
        print(f"Label removed from snapshot '{args.snapshot_id}'.")
        return 0
    print(f"No label found for snapshot '{args.snapshot_id}'.")
    return 1


def cmd_label_get(args: argparse.Namespace) -> int:
    label = labeler.get_label(args.storage_dir, args.snapshot_id)
    if label is None:
        print(f"No label for snapshot '{args.snapshot_id}'.")
        return 1
    print(label)
    return 0


def cmd_label_list(args: argparse.Namespace) -> int:
    labels = labeler.list_labels(args.storage_dir)
    if not labels:
        print("No labels defined.")
        return 0
    for sid, lbl in sorted(labels.items()):
        print(f"{sid}: {lbl}")
    return 0


def cmd_label_find(args: argparse.Namespace) -> int:
    ids = labeler.find_by_label(args.storage_dir, args.label)
    if not ids:
        print(f"No snapshots with label '{args.label}'.")
        return 0
    for sid in sorted(ids):
        print(sid)
    return 0


def register_label_commands(subparsers: argparse._SubParsersAction, parent: argparse.ArgumentParser) -> None:
    p_set = subparsers.add_parser("label-set", parents=[parent], help="Set a label on a snapshot")
    p_set.add_argument("snapshot_id")
    p_set.add_argument("label")
    p_set.set_defaults(func=cmd_label_set)

    p_rm = subparsers.add_parser("label-remove", parents=[parent], help="Remove a label from a snapshot")
    p_rm.add_argument("snapshot_id")
    p_rm.set_defaults(func=cmd_label_remove)

    p_get = subparsers.add_parser("label-get", parents=[parent], help="Get label for a snapshot")
    p_get.add_argument("snapshot_id")
    p_get.set_defaults(func=cmd_label_get)

    p_list = subparsers.add_parser("label-list", parents=[parent], help="List all labels")
    p_list.set_defaults(func=cmd_label_list)

    p_find = subparsers.add_parser("label-find", parents=[parent], help="Find snapshots by label")
    p_find.add_argument("label")
    p_find.set_defaults(func=cmd_label_find)
