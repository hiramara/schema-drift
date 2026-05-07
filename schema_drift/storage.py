"""Persistence layer for schema snapshots — save/load snapshots to/from JSON files."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from schema_drift.snapshot import DatabaseSnapshot, from_dict, to_dict

DEFAULT_SNAPSHOT_DIR = ".schema_drift"


def _snapshot_filename(snapshot_id: str) -> str:
    """Return a safe filename for a given snapshot ID."""
    safe = snapshot_id.replace(" ", "_").replace("/", "-")
    return f"{safe}.json"


def save_snapshot(snapshot: DatabaseSnapshot, directory: str = DEFAULT_SNAPSHOT_DIR) -> Path:
    """Persist *snapshot* as a JSON file inside *directory*.

    Returns the path of the written file.
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)

    filename = _snapshot_filename(snapshot.snapshot_id)
    file_path = dir_path / filename

    with file_path.open("w", encoding="utf-8") as fh:
        json.dump(to_dict(snapshot), fh, indent=2)

    return file_path


def load_snapshot(snapshot_id: str, directory: str = DEFAULT_SNAPSHOT_DIR) -> DatabaseSnapshot:
    """Load and return the snapshot identified by *snapshot_id* from *directory*.

    Raises FileNotFoundError when the snapshot does not exist.
    """
    file_path = Path(directory) / _snapshot_filename(snapshot_id)

    if not file_path.exists():
        raise FileNotFoundError(f"Snapshot '{snapshot_id}' not found in '{directory}'")

    with file_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    return from_dict(data)


def list_snapshots(directory: str = DEFAULT_SNAPSHOT_DIR) -> List[str]:
    """Return a sorted list of snapshot IDs available in *directory*."""
    dir_path = Path(directory)
    if not dir_path.exists():
        return []

    ids = []
    for entry in sorted(dir_path.iterdir()):
        if entry.suffix == ".json" and entry.is_file():
            # Reverse the filename transformation to recover the original ID
            snapshot_id = entry.stem.replace("_", " ").replace("-", "/")
            ids.append(snapshot_id)
    return ids


def latest_snapshot(directory: str = DEFAULT_SNAPSHOT_DIR) -> Optional[DatabaseSnapshot]:
    """Return the most recently saved snapshot, or *None* if none exist."""
    ids = list_snapshots(directory)
    if not ids:
        return None
    return load_snapshot(ids[-1], directory=directory)
