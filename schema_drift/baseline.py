"""Baseline management: mark a snapshot as the accepted baseline for drift comparison."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

BASELINE_FILENAME = ".schema_drift_baseline"


def _baseline_path(storage_dir: str) -> Path:
    return Path(storage_dir) / BASELINE_FILENAME


def set_baseline(storage_dir: str, snapshot_id: str) -> None:
    """Persist *snapshot_id* as the current baseline."""
    path = _baseline_path(storage_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"baseline_id": snapshot_id}, fh, indent=2)


def get_baseline(storage_dir: str) -> Optional[str]:
    """Return the current baseline snapshot id, or *None* if none is set."""
    path = _baseline_path(storage_dir)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("baseline_id")


def clear_baseline(storage_dir: str) -> bool:
    """Remove the baseline file.  Returns *True* if a file was removed."""
    path = _baseline_path(storage_dir)
    if path.exists():
        os.remove(path)
        return True
    return False


def baseline_info(storage_dir: str) -> dict:
    """Return a dict suitable for serialisation describing the current baseline."""
    bid = get_baseline(storage_dir)
    return {
        "baseline_id": bid,
        "is_set": bid is not None,
        "storage_dir": str(storage_dir),
    }
