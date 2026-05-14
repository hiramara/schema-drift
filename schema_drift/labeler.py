"""Labeler: attach and manage human-readable labels on snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_LABELS_FILE = "labels.json"


def _labels_path(storage_dir: str) -> Path:
    return Path(storage_dir) / _LABELS_FILE


def _load(storage_dir: str) -> Dict[str, str]:
    path = _labels_path(storage_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save(storage_dir: str, data: Dict[str, str]) -> None:
    _labels_path(storage_dir).write_text(json.dumps(data, indent=2))


def set_label(storage_dir: str, snapshot_id: str, label: str) -> None:
    """Attach or overwrite a label for *snapshot_id*."""
    data = _load(storage_dir)
    data[snapshot_id] = label
    _save(storage_dir, data)


def remove_label(storage_dir: str, snapshot_id: str) -> bool:
    """Remove the label for *snapshot_id*. Returns True if it existed."""
    data = _load(storage_dir)
    if snapshot_id not in data:
        return False
    del data[snapshot_id]
    _save(storage_dir, data)
    return True


def get_label(storage_dir: str, snapshot_id: str) -> Optional[str]:
    """Return the label for *snapshot_id*, or None."""
    return _load(storage_dir).get(snapshot_id)


def list_labels(storage_dir: str) -> Dict[str, str]:
    """Return all snapshot_id -> label mappings."""
    return dict(_load(storage_dir))


def find_by_label(storage_dir: str, label: str) -> List[str]:
    """Return all snapshot IDs whose label matches *label* exactly."""
    return [sid for sid, lbl in _load(storage_dir).items() if lbl == label]
