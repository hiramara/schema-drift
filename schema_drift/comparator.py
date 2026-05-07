"""Snapshot comparator: finds the most recent pair of snapshots and produces a diff summary."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .differ import SchemaChange, diff_tables
from .snapshot import DatabaseSnapshot
from .storage import list_snapshots, load_snapshot


@dataclass
class ComparisonResult:
    """Holds the outcome of comparing two snapshots."""

    old_snapshot: DatabaseSnapshot
    new_snapshot: DatabaseSnapshot
    changes: List[SchemaChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def change_count(self) -> int:
        return len(self.changes)

    def to_dict(self) -> dict:
        return {
            "old_snapshot_id": self.old_snapshot.snapshot_id,
            "new_snapshot_id": self.new_snapshot.snapshot_id,
            "has_changes": self.has_changes,
            "change_count": self.change_count,
            "changes": [c.to_dict() for c in self.changes],
        }


def compare_snapshots(
    old_snapshot: DatabaseSnapshot,
    new_snapshot: DatabaseSnapshot,
) -> ComparisonResult:
    """Diff two DatabaseSnapshot objects and return a ComparisonResult."""
    changes = diff_tables(old_snapshot.tables, new_snapshot.tables)
    return ComparisonResult(
        old_snapshot=old_snapshot,
        new_snapshot=new_snapshot,
        changes=changes,
    )


def compare_latest_two(storage_dir: str) -> Optional[ComparisonResult]:
    """Load the two most recent snapshots from *storage_dir* and compare them.

    Returns ``None`` when fewer than two snapshots are available.
    """
    ids = list_snapshots(storage_dir)
    if len(ids) < 2:
        return None
    old_snapshot = load_snapshot(storage_dir, ids[-2])
    new_snapshot = load_snapshot(storage_dir, ids[-1])
    return compare_snapshots(old_snapshot, new_snapshot)
