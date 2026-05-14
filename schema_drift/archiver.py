"""Archiver: mark snapshots as archived and list/restore them."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

_ARCHIVE_FILE = "archive_index.json"


def _archive_path(storage_dir: str) -> Path:
    return Path(storage_dir) / _ARCHIVE_FILE


def _load_index(storage_dir: str) -> dict:
    path = _archive_path(storage_dir)
    if not path.exists():
        return {"archived": []}
    with path.open() as fh:
        return json.load(fh)


def _save_index(storage_dir: str, index: dict) -> None:
    path = _archive_path(storage_dir)
    Path(storage_dir).mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(index, fh, indent=2)


def archive_snapshot(storage_dir: str, snapshot_id: str) -> bool:
    """Mark *snapshot_id* as archived.  Returns True if newly added."""
    index = _load_index(storage_dir)
    if snapshot_id in index["archived"]:
        return False
    index["archived"].append(snapshot_id)
    _save_index(storage_dir, index)
    return True


def unarchive_snapshot(storage_dir: str, snapshot_id: str) -> bool:
    """Remove *snapshot_id* from the archive list.  Returns True if removed."""
    index = _load_index(storage_dir)
    if snapshot_id not in index["archived"]:
        return False
    index["archived"].remove(snapshot_id)
    _save_index(storage_dir, index)
    return True


def list_archived(storage_dir: str) -> List[str]:
    """Return all snapshot IDs currently marked as archived."""
    return list(_load_index(storage_dir)["archived"])


def is_archived(storage_dir: str, snapshot_id: str) -> bool:
    """Return True if *snapshot_id* is in the archive list."""
    return snapshot_id in _load_index(storage_dir)["archived"]


def clear_archive(storage_dir: str) -> int:
    """Remove all entries from the archive index.  Returns count removed."""
    index = _load_index(storage_dir)
    count = len(index["archived"])
    index["archived"] = []
    _save_index(storage_dir, index)
    return count
