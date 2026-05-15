"""CLI commands for the migration planner."""

from __future__ import annotations

import argparse
import json
import sys

from schema_drift.storage import load_snapshot
from schema_drift.differ import diff_tables
from schema_drift.planner import plan_migration


def cmd_plan(args: argparse.Namespace) -> int:
    from_snap = load_snapshot(args.storage_dir, args.from_snapshot)
    if from_snap is None:
        print(f"Snapshot not found: {args.from_snapshot}", file=sys.stderr)
        return 2

    to_snap = load_snapshot(args.storage_dir, args.to_snapshot)
    if to_snap is None:
        print(f"Snapshot not found: {args.to_snapshot}", file=sys.stderr)
        return 2

    changes = diff_tables(from_snap, to_snap)
    plan = plan_migration(changes)

    if args.format == "json":
        print(json.dumps(plan.to_dict(), indent=2))
        return 0

    if plan.step_count == 0:
        print("No migration steps required.")
        return 0

    print(f"Migration plan: {plan.step_count} step(s)\n")
    for step in plan.steps:
        print(f"  [{step.order}] {step.change_type} — {step.table}")
        print(f"       {step.description}")
        print(f"       {step.sql_hint}")
        print()

    return 0


def register_plan_commands(
    subparsers: argparse._SubParsersAction,
    parent_parser: argparse.ArgumentParser,
) -> None:
    p = subparsers.add_parser("plan", parents=[parent_parser], help="Generate migration plan from a diff")
    p.add_argument("from_snapshot", help="Snapshot ID to migrate from")
    p.add_argument("to_snapshot", help="Snapshot ID to migrate to")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_plan)
