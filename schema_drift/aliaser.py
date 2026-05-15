"""Snapshot aliasing — assign human-friendly aliases to snapshot IDs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


def _aliases_path(storage_dir: str) -> Path:
    return Path(storage_dir) / "aliases.json"


def _load(storage_dir: str) -> Dict[str, str]:
    path = _aliases_path(storage_dir)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def _save(storage_dir: str, data: Dict[str, str]) -> None:
    path = _aliases_path(storage_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


def set_alias(storage_dir: str, alias: str, snapshot_id: str) -> None:
    """Assign *alias* to *snapshot_id*, overwriting any previous mapping."""
    data = _load(storage_dir)
    data[alias] = snapshot_id
    _save(storage_dir, data)


def remove_alias(storage_dir: str, alias: str) -> bool:
    """Remove *alias*. Returns True if it existed, False otherwise."""
    data = _load(storage_dir)
    if alias not in data:
        return False
    del data[alias]
    _save(storage_dir, data)
    return True


def resolve_alias(storage_dir: str, alias: str) -> Optional[str]:
    """Return the snapshot ID for *alias*, or None if not found."""
    return _load(storage_dir).get(alias)


def list_aliases(storage_dir: str) -> List[Dict[str, str]]:
    """Return all aliases as a list of {alias, snapshot_id} dicts."""
    data = _load(storage_dir)
    return [{"alias": k, "snapshot_id": v} for k, v in sorted(data.items())]


def find_aliases_for(storage_dir: str, snapshot_id: str) -> List[str]:
    """Return all aliases that point to *snapshot_id*."""
    data = _load(storage_dir)
    return [alias for alias, sid in data.items() if sid == snapshot_id]
