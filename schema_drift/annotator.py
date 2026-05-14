"""Annotator: attach human-readable notes to snapshots."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_ANNOTATIONS_FILE = "annotations.json"


def _annotations_path(storage_dir: str) -> Path:
    return Path(storage_dir) / _ANNOTATIONS_FILE


def _load(storage_dir: str) -> Dict[str, List[str]]:
    path = _annotations_path(storage_dir)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def _save(storage_dir: str, data: Dict[str, List[str]]) -> None:
    path = _annotations_path(storage_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


def add_annotation(storage_dir: str, snapshot_id: str, note: str) -> None:
    """Append *note* to the annotation list for *snapshot_id*."""
    data = _load(storage_dir)
    data.setdefault(snapshot_id, [])
    if note not in data[snapshot_id]:
        data[snapshot_id].append(note)
    _save(storage_dir, data)


def remove_annotation(storage_dir: str, snapshot_id: str, note: str) -> bool:
    """Remove *note* from *snapshot_id*. Returns True if it existed."""
    data = _load(storage_dir)
    notes = data.get(snapshot_id, [])
    if note not in notes:
        return False
    notes.remove(note)
    data[snapshot_id] = notes
    _save(storage_dir, data)
    return True


def get_annotations(storage_dir: str, snapshot_id: str) -> List[str]:
    """Return all notes attached to *snapshot_id*."""
    return _load(storage_dir).get(snapshot_id, [])


def all_annotations(storage_dir: str) -> Dict[str, List[str]]:
    """Return the full annotations mapping."""
    return _load(storage_dir)


def clear_annotations(storage_dir: str, snapshot_id: Optional[str] = None) -> None:
    """Clear annotations for one snapshot or all snapshots."""
    if snapshot_id is None:
        _save(storage_dir, {})
    else:
        data = _load(storage_dir)
        data.pop(snapshot_id, None)
        _save(storage_dir, data)
