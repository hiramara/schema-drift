"""CLI commands for schedule management."""

from __future__ import annotations

import argparse
import sys

from schema_drift.scheduler import ScheduleConfig, load_schedule_config, save_schedule_config


def cmd_schedule_init(args: argparse.Namespace) -> int:
    """Create a new schedule config file."""
    config = ScheduleConfig(
        interval_seconds=args.interval,
        storage_dir=args.storage_dir,
        snapshot_id_prefix=args.prefix,
        notify_on_drift=args.notify,
        max_snapshots=args.max_snapshots,
    )
    save_schedule_config(config, args.config)
    print(f"Schedule config written to {args.config}")
    return 0


def cmd_schedule_show(args: argparse.Namespace) -> int:
    """Display an existing schedule config."""
    try:
        config = load_schedule_config(args.config)
    except FileNotFoundError:
        print(f"Config not found: {args.config}", file=sys.stderr)
        return 2
    for key, value in config.to_dict().items():
        print(f"{key}: {value}")
    return 0


def register_schedule_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # schedule-init
    p_init = subparsers.add_parser("schedule-init", help="Create a schedule config")
    p_init.add_argument("--config", default="schedule.json", help="Path to config file")
    p_init.add_argument("--interval", type=int, default=3600, help="Seconds between snapshots")
    p_init.add_argument("--storage-dir", default="snapshots", help="Snapshot storage directory")
    p_init.add_argument("--prefix", default="scheduled", help="Snapshot ID prefix")
    p_init.add_argument("--notify", action="store_true", help="Notify on drift")
    p_init.add_argument("--max-snapshots", type=int, default=50, dest="max_snapshots")
    p_init.set_defaults(func=cmd_schedule_init)

    # schedule-show
    p_show = subparsers.add_parser("schedule-show", help="Show a schedule config")
    p_show.add_argument("--config", default="schedule.json", help="Path to config file")
    p_show.set_defaults(func=cmd_schedule_show)
