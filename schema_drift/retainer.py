"""Retention policy: automatically expire old snapshots beyond a configured limit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from schema_drift.storage import list_snapshots, _snapshot_filename

_POLICY_FILE = "retention_policy.json"


def _policy_path(storage_dir: str) -> Path:
    return Path(storage_dir) / _POLICY_FILE


def load_policy(storage_dir: str) -> dict:
    """Load retention policy from storage_dir, returning defaults if absent."""
    path = _policy_path(storage_dir)
    if not path.exists():
        return {"max_snapshots": None, "keep_pinned": True}
    with path.open() as fh:
        return json.load(fh)


def save_policy(storage_dir: str, max_snapshots: Optional[int], keep_pinned: bool = True) -> None:
    """Persist a retention policy to storage_dir."""
    path = _policy_path(storage_dir)
    Path(storage_dir).mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump({"max_snapshots": max_snapshots, "keep_pinned": keep_pinned}, fh, indent=2)


def apply_retention(
    storage_dir: str,
    pinned_ids: Optional[List[str]] = None,
) -> List[str]:
    """Delete snapshots that exceed the retention limit.

    Snapshots are ordered oldest-first (alphabetical by filename).  The
    newest ``max_snapshots`` are kept; the rest are deleted unless they
    appear in *pinned_ids* and ``keep_pinned`` is True.

    Returns the list of snapshot IDs that were removed.
    """
    policy = load_policy(storage_dir)
    max_snapshots = policy.get("max_snapshots")
    keep_pinned = policy.get("keep_pinned", True)

    if max_snapshots is None or max_snapshots <= 0:
        return []

    ids = list_snapshots(storage_dir)  # already sorted newest-first by storage
    # Reverse so oldest are first for trimming
    ids_oldest_first = list(reversed(ids))

    pinned = set(pinned_ids or [])
    removed: List[str] = []

    # Walk from oldest; remove until we are within the limit
    kept = list(ids_oldest_first)  # copy we will mutate
    while len(kept) > max_snapshots:
        candidate = kept[0]
        if keep_pinned and candidate in pinned:
            # Skip pinned; try next oldest
            kept.append(kept.pop(0))
            # Safety: if all remaining are pinned we cannot trim further
            if all(s in pinned for s in kept[: len(kept) - max_snapshots + 1]):
                break
            continue
        kept.pop(0)
        file_path = Path(storage_dir) / _snapshot_filename(candidate)
        if file_path.exists():
            file_path.unlink()
        removed.append(candidate)

    return removed
