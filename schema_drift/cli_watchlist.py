"""CLI commands for managing the drift watchlist."""

from __future__ import annotations

import argparse

from schema_drift import watchlist


def cmd_watch_add(args: argparse.Namespace) -> int:
    added = watchlist.add_watch(
        args.storage_dir,
        table=args.table,
        column=args.column or None,
        reason=args.reason or None,
    )
    if added:
        target = f"{args.table}.{args.column}" if args.column else args.table
        print(f"Added to watchlist: {target}")
    else:
        print("Entry already on watchlist.")
    return 0


def cmd_watch_remove(args: argparse.Namespace) -> int:
    removed = watchlist.remove_watch(
        args.storage_dir,
        table=args.table,
        column=args.column or None,
    )
    if removed:
        target = f"{args.table}.{args.column}" if args.column else args.table
        print(f"Removed from watchlist: {target}")
    else:
        print("Entry not found in watchlist.")
    return 0


def cmd_watch_list(args: argparse.Namespace) -> int:
    entries = watchlist.list_watches(args.storage_dir)
    if not entries:
        print("Watchlist is empty.")
        return 0
    for e in entries:
        target = f"{e['table']}.{e['column']}" if e["column"] else e["table"]
        reason = f"  # {e['reason']}" if e["reason"] else ""
        print(f"  {target}{reason}")
    return 0


def cmd_watch_clear(args: argparse.Namespace) -> int:
    count = watchlist.clear_watchlist(args.storage_dir)
    print(f"Cleared {count} watchlist entries.")
    return 0


def register_watchlist_commands(subparsers, parent_parser) -> None:
    w = subparsers.add_parser("watch", help="Manage the drift watchlist")
    wsub = w.add_subparsers(dest="watch_cmd")

    p_add = wsub.add_parser("add", parents=[parent_parser], help="Add table/column to watchlist")
    p_add.add_argument("table")
    p_add.add_argument("--column", default="")
    p_add.add_argument("--reason", default="")
    p_add.set_defaults(func=cmd_watch_add)

    p_rm = wsub.add_parser("remove", parents=[parent_parser], help="Remove entry from watchlist")
    p_rm.add_argument("table")
    p_rm.add_argument("--column", default="")
    p_rm.set_defaults(func=cmd_watch_remove)

    p_ls = wsub.add_parser("list", parents=[parent_parser], help="List watchlist entries")
    p_ls.set_defaults(func=cmd_watch_list)

    p_cl = wsub.add_parser("clear", parents=[parent_parser], help="Clear all watchlist entries")
    p_cl.set_defaults(func=cmd_watch_clear)
