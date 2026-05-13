"""Tag snapshots with arbitrary labels for easier organisation and retrieval."""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional


def _tags_path(storage_dir: str) -> str:
    return os.path.join(storage_dir, "tags.json")


def _load_tags(storage_dir: str) -> Dict[str, List[str]]:
    """Return mapping of snapshot_id -> list[tag]."""
    path = _tags_path(storage_dir)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_tags(storage_dir: str, tags: Dict[str, List[str]]) -> None:
    path = _tags_path(storage_dir)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(tags, fh, indent=2)


def add_tag(storage_dir: str, snapshot_id: str, tag: str) -> None:
    """Add *tag* to *snapshot_id*.  No-op if already present."""
    tags = _load_tags(storage_dir)
    current = tags.get(snapshot_id, [])
    if tag not in current:
        current.append(tag)
    tags[snapshot_id] = current
    _save_tags(storage_dir, tags)


def remove_tag(storage_dir: str, snapshot_id: str, tag: str) -> bool:
    """Remove *tag* from *snapshot_id*.  Returns True if the tag existed."""
    tags = _load_tags(storage_dir)
    current = tags.get(snapshot_id, [])
    if tag not in current:
        return False
    current.remove(tag)
    tags[snapshot_id] = current
    _save_tags(storage_dir, tags)
    return True


def get_tags(storage_dir: str, snapshot_id: str) -> List[str]:
    """Return all tags for *snapshot_id*."""
    return _load_tags(storage_dir).get(snapshot_id, [])


def find_by_tag(storage_dir: str, tag: str) -> List[str]:
    """Return all snapshot IDs that carry *tag*."""
    tags = _load_tags(storage_dir)
    return [sid for sid, t_list in tags.items() if tag in t_list]


def all_tags(storage_dir: str) -> Dict[str, List[str]]:
    """Return the full tag mapping."""
    return _load_tags(storage_dir)


def clear_tags(storage_dir: str, snapshot_id: str) -> None:
    """Remove every tag from *snapshot_id*."""
    tags = _load_tags(storage_dir)
    tags.pop(snapshot_id, None)
    _save_tags(storage_dir, tags)
