"""Trace the history of a specific column or table across snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from schema_drift.snapshot import DatabaseSnapshot


@dataclass
class TraceEntry:
    snapshot_id: str
    table: str
    column: Optional[str]
    exists: bool
    detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "table": self.table,
            "column": self.column,
            "exists": self.exists,
            "detail": self.detail,
        }


@dataclass
class TraceResult:
    table: str
    column: Optional[str]
    entries: List[TraceEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "column": self.column,
            "entries": [e.to_dict() for e in self.entries],
        }


def trace_table(
    snapshots: List[DatabaseSnapshot],
    table: str,
) -> TraceResult:
    """Return presence/absence of *table* across ordered snapshots."""
    entries: List[TraceEntry] = []
    for snap in snapshots:
        tbl = snap.tables.get(table)
        exists = tbl is not None
        detail = {"columns": len(tbl.columns) if tbl else 0}
        entries.append(TraceEntry(snap.snapshot_id, table, None, exists, detail))
    return TraceResult(table=table, column=None, entries=entries)


def trace_column(
    snapshots: List[DatabaseSnapshot],
    table: str,
    column: str,
) -> TraceResult:
    """Return presence/absence and type of *column* in *table* across snapshots."""
    entries: List[TraceEntry] = []
    for snap in snapshots:
        tbl = snap.tables.get(table)
        col = tbl.columns.get(column) if tbl else None
        exists = col is not None
        detail = {"type": col.col_type if col else None,
                  "nullable": col.nullable if col else None}
        entries.append(TraceEntry(snap.snapshot_id, table, column, exists, detail))
    return TraceResult(table=table, column=column, entries=entries)
