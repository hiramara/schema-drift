"""CLI sub-commands for managing ignore rules."""

from __future__ import annotations

import argparse
import json
import sys

from schema_drift.ignorer import IgnoreConfig, IgnoreRule, load_ignore_config, save_ignore_config

_DEFAULT_PATH = ".schema_drift_ignore.json"


def cmd_ignore_add(args: argparse.Namespace) -> int:
    config = load_ignore_config(args.ignore_file)
    rule = IgnoreRule(
        table=args.table or None,
        column=args.column or None,
        change_type=args.change_type or None,
        reason=args.reason or "",
    )
    config.rules.append(rule)
    save_ignore_config(config, args.ignore_file)
    print(f"Added ignore rule ({len(config.rules)} total in {args.ignore_file}).")
    return 0


def cmd_ignore_list(args: argparse.Namespace) -> int:
    config = load_ignore_config(args.ignore_file)
    if not config.rules:
        print("No ignore rules defined.")
        return 0
    for i, rule in enumerate(config.rules, 1):
        parts = []
        if rule.table:
            parts.append(f"table={rule.table}")
        if rule.column:
            parts.append(f"column={rule.column}")
        if rule.change_type:
            parts.append(f"type={rule.change_type}")
        desc = ", ".join(parts) if parts else "(catch-all)"
        reason = f" — {rule.reason}" if rule.reason else ""
        print(f"  [{i}] {desc}{reason}")
    return 0


def cmd_ignore_clear(args: argparse.Namespace) -> int:
    save_ignore_config(IgnoreConfig(), args.ignore_file)
    print(f"All ignore rules cleared from {args.ignore_file}.")
    return 0


def register_ignore_commands(subparsers: argparse._SubParsersAction) -> None:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--ignore-file", default=_DEFAULT_PATH, metavar="PATH")

    # ignore add
    p_add = subparsers.add_parser("ignore-add", parents=[parent], help="Add an ignore rule")
    p_add.add_argument("--table", default="")
    p_add.add_argument("--column", default="")
    p_add.add_argument("--change-type", default="", dest="change_type")
    p_add.add_argument("--reason", default="")
    p_add.set_defaults(func=cmd_ignore_add)

    # ignore list
    p_list = subparsers.add_parser("ignore-list", parents=[parent], help="List ignore rules")
    p_list.set_defaults(func=cmd_ignore_list)

    # ignore clear
    p_clear = subparsers.add_parser("ignore-clear", parents=[parent], help="Remove all ignore rules")
    p_clear.set_defaults(func=cmd_ignore_clear)
