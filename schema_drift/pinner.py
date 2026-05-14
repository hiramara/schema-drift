"""Snapshot pinning — mark snapshots as pinned so they are protected from
automatic cleanup / archiving and are easy to retrieve by name."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_PINS_FILE = "pins.json"


def _pins_path(storage_dir: str) -> Path:
    return Path(storage_dir) / _PINS_FILE


def _load(storage_dir: str) -> Dict[str, str]:
    """Return {snapshot_id: label} mapping."""
    p = _pins_path(storage_dir)
    if not p.exists():
        return {}
    with p.open() as fh:
        return json.load(fh)


def _save(storage_dir: str, pins: Dict[str, str]) -> None:
    p = _pins_path(storage_dir)
    with p.open("w") as fh:
        json.dump(pins, fh, indent=2)


def pin_snapshot(storage_dir: str, snapshot_id: str, label: str = "") -> bool:
    """Pin *snapshot_id* with an optional human-readable *label*.

    Returns True if the snapshot was newly pinned, False if it was already
    pinned (label is updated in both cases).
    """
    pins = _load(storage_dir)
    already = snapshot_id in pins
    pins[snapshot_id] = label
    _save(storage_dir, pins)
    return not already


def unpin_snapshot(storage_dir: str, snapshot_id: str) -> bool:
    """Remove the pin for *snapshot_id*.

    Returns True if the pin existed and was removed, False otherwise.
    """
    pins = _load(storage_dir)
    if snapshot_id not in pins:
        return False
    del pins[snapshot_id]
    _save(storage_dir, pins)
    return True


def is_pinned(storage_dir: str, snapshot_id: str) -> bool:
    """Return True if *snapshot_id* is currently pinned."""
    return snapshot_id in _load(storage_dir)


def list_pins(storage_dir: str) -> List[Dict[str, str]]:
    """Return a list of dicts with 'id' and 'label' keys, sorted by id."""
    pins = _load(storage_dir)
    return [{"id": sid, "label": label} for sid, label in sorted(pins.items())]


def get_label(storage_dir: str, snapshot_id: str) -> Optional[str]:
    """Return the label for *snapshot_id*, or None if not pinned."""
    pins = _load(storage_dir)
    return pins.get(snapshot_id)
