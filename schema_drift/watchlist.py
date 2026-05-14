"""Watchlist: track specific tables/columns of interest for priority drift alerting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def _watchlist_path(storage_dir: str) -> Path:
    return Path(storage_dir) / "watchlist.json"


def _load(storage_dir: str) -> dict:
    p = _watchlist_path(storage_dir)
    if not p.exists():
        return {"entries": []}
    return json.loads(p.read_text())


def _save(storage_dir: str, data: dict) -> None:
    p = _watchlist_path(storage_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def add_watch(storage_dir: str, table: str, column: Optional[str] = None, reason: Optional[str] = None) -> bool:
    """Add a table or column to the watchlist. Returns True if newly added."""
    data = _load(storage_dir)
    entry = {"table": table, "column": column, "reason": reason or ""}
    for existing in data["entries"]:
        if existing["table"] == table and existing["column"] == column:
            return False
    data["entries"].append(entry)
    _save(storage_dir, data)
    return True


def remove_watch(storage_dir: str, table: str, column: Optional[str] = None) -> bool:
    """Remove a watchlist entry. Returns True if it existed."""
    data = _load(storage_dir)
    before = len(data["entries"])
    data["entries"] = [
        e for e in data["entries"]
        if not (e["table"] == table and e["column"] == column)
    ]
    if len(data["entries"]) == before:
        return False
    _save(storage_dir, data)
    return True


def list_watches(storage_dir: str) -> list[dict]:
    """Return all watchlist entries."""
    return _load(storage_dir)["entries"]


def is_watched(storage_dir: str, table: str, column: Optional[str] = None) -> bool:
    """Return True if the given table (and optionally column) is on the watchlist."""
    for entry in list_watches(storage_dir):
        if entry["table"] == table and entry["column"] == column:
            return True
    return False


def clear_watchlist(storage_dir: str) -> int:
    """Remove all entries. Returns count removed."""
    data = _load(storage_dir)
    count = len(data["entries"])
    _save(storage_dir, {"entries": []})
    return count
