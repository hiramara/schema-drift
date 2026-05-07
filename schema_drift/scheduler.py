"""Periodic snapshot scheduling and drift detection."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


@dataclass
class ScheduleConfig:
    interval_seconds: int
    storage_dir: str
    snapshot_id_prefix: str = "scheduled"
    notify_on_drift: bool = False
    max_snapshots: int = 50
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleConfig":
        return cls(
            interval_seconds=int(data["interval_seconds"]),
            storage_dir=data["storage_dir"],
            snapshot_id_prefix=data.get("snapshot_id_prefix", "scheduled"),
            notify_on_drift=bool(data.get("notify_on_drift", False)),
            max_snapshots=int(data.get("max_snapshots", 50)),
            extra=data.get("extra", {}),
        )

    def to_dict(self) -> dict:
        return {
            "interval_seconds": self.interval_seconds,
            "storage_dir": self.storage_dir,
            "snapshot_id_prefix": self.snapshot_id_prefix,
            "notify_on_drift": self.notify_on_drift,
            "max_snapshots": self.max_snapshots,
            "extra": self.extra,
        }


def load_schedule_config(path: str) -> ScheduleConfig:
    """Load a ScheduleConfig from a JSON file."""
    with open(path, "r") as fh:
        data = json.load(fh)
    return ScheduleConfig.from_dict(data)


def save_schedule_config(config: ScheduleConfig, path: str) -> None:
    """Persist a ScheduleConfig to a JSON file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(config.to_dict(), fh, indent=2)


def run_once(
    config: ScheduleConfig,
    snapshot_fn: Callable[[str, str], None],
    timestamp: Optional[int] = None,
) -> str:
    """Execute a single scheduled snapshot tick.

    Returns the snapshot id that was saved.
    """
    ts = timestamp if timestamp is not None else int(time.time())
    snapshot_id = f"{config.snapshot_id_prefix}-{ts}"
    snapshot_fn(snapshot_id, config.storage_dir)
    return snapshot_id
