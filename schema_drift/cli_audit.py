"""CLI commands for viewing and managing the audit log."""

from __future__ import annotations

import argparse
import json
import sys

from schema_drift.auditor import get_audit_log, clear_audit_log


def cmd_audit_log(args: argparse.Namespace) -> int:
    """Print audit log entries to stdout."""
    entries = get_audit_log(args.storage_dir)
    if not entries:
        print("No audit log entries found.")
        return 0

    if getattr(args, "json", False):
        print(json.dumps([e.to_dict() for e in entries], indent=2))
        return 0

    for entry in entries:
        detail_str = ""
        if entry.details:
            detail_str = "  " + ", ".join(f"{k}={v}" for k, v in entry.details.items())
        print(f"[{entry.timestamp}] {entry.event}{detail_str}")
    return 0


def cmd_audit_clear(args: argparse.Namespace) -> int:
    """Clear all audit log entries."""
    clear_audit_log(args.storage_dir)
    print("Audit log cleared.")
    return 0


def register_audit_commands(
    subparsers: argparse._SubParsersAction,
    parent_parser: argparse.ArgumentParser,
) -> None:
    audit_p = subparsers.add_parser("audit", help="Manage the audit log")
    audit_sub = audit_p.add_subparsers(dest="audit_cmd")

    log_p = audit_sub.add_parser("log", parents=[parent_parser], help="Show audit log")
    log_p.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )
    log_p.set_defaults(func=cmd_audit_log)

    clear_p = audit_sub.add_parser(
        "clear", parents=[parent_parser], help="Clear audit log"
    )
    clear_p.set_defaults(func=cmd_audit_clear)
