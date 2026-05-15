"""Deduplicator: removes duplicate SchemaChange entries from a diff list.

Two changes are considered duplicates when they share the same table, column,
change_type, and (for modifications) the same before/after values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from schema_drift.differ import SchemaChange


@dataclass
class DeduplicationResult:
    original_count: int
    deduplicated: List[SchemaChange]
    removed_count: int

    def to_dict(self) -> dict:
        return {
            "original_count": self.original_count,
            "deduplicated_count": len(self.deduplicated),
            "removed_count": self.removed_count,
            "changes": [c.to_dict() for c in self.deduplicated],
        }


def _change_key(change: SchemaChange) -> Tuple:
    """Return a hashable key that uniquely identifies a change."""
    before = change.before or {}
    after = change.after or {}
    return (
        change.table,
        change.column or "",
        change.change_type.value,
        tuple(sorted(before.items())),
        tuple(sorted(after.items())),
    )


def deduplicate_changes(changes: List[SchemaChange]) -> DeduplicationResult:
    """Remove duplicate changes, preserving first-occurrence order."""
    seen: set = set()
    unique: List[SchemaChange] = []

    for change in changes:
        key = _change_key(change)
        if key not in seen:
            seen.add(key)
            unique.append(change)

    return DeduplicationResult(
        original_count=len(changes),
        deduplicated=unique,
        removed_count=len(changes) - len(unique),
    )
