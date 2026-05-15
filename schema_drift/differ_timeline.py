"""Build a timeline of schema changes across multiple snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from schema_drift.differ import SchemaChange, diff_tables
from schema_drift.snapshot import DatabaseSnapshot


@dataclass
class TimelineEntry:
    """A single step in the schema change timeline."""

    from_id: str
    to_id: str
    changes: List[SchemaChange] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "change_count": len(self.changes),
            "changes": [c.to_dict() for c in self.changes],
        }


@dataclass
class SchemaTimeline:
    """Ordered sequence of diff entries across a series of snapshots."""

    entries: List[TimelineEntry] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return sum(len(e.changes) for e in self.entries)

    @property
    def snapshot_ids(self) -> List[str]:
        if not self.entries:
            return []
        ids = [self.entries[0].from_id]
        for entry in self.entries:
            ids.append(entry.to_id)
        return ids

    def changes_for_table(self, table: str) -> List[SchemaChange]:
        return [
            c
            for entry in self.entries
            for c in entry.changes
            if c.table == table
        ]

    def to_dict(self) -> Dict:
        return {
            "snapshot_ids": self.snapshot_ids,
            "total_changes": self.total_changes,
            "entries": [e.to_dict() for e in self.entries],
        }


def build_timeline(snapshots: List[DatabaseSnapshot]) -> SchemaTimeline:
    """Compute a timeline by diffing consecutive snapshots.

    Args:
        snapshots: Ordered list of snapshots (oldest first).

    Returns:
        SchemaTimeline with one entry per consecutive pair.

    Raises:
        ValueError: If fewer than two snapshots are provided.
    """
    if len(snapshots) < 2:
        raise ValueError("At least two snapshots are required to build a timeline.")

    entries: List[TimelineEntry] = []
    for prev, curr in zip(snapshots, snapshots[1:]):
        changes = diff_tables(prev.tables, curr.tables)
        entries.append(
            TimelineEntry(
                from_id=prev.snapshot_id,
                to_id=curr.snapshot_id,
                changes=changes,
            )
        )
    return SchemaTimeline(entries=entries)
