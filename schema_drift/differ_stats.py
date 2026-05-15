"""Compute statistical summaries over a list of SchemaChange objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from schema_drift.differ import SchemaChange, ChangeType


@dataclass
class DiffStats:
    total: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_table: Dict[str, int] = field(default_factory=dict)
    tables_affected: int = 0

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "by_type": self.by_type,
            "by_table": self.by_table,
            "tables_affected": self.tables_affected,
        }


def compute_diff_stats(changes: List[SchemaChange]) -> DiffStats:
    """Return a DiffStats summary for *changes*."""
    by_type: Dict[str, int] = {}
    by_table: Dict[str, int] = {}

    for change in changes:
        type_key = change.change_type.value
        by_type[type_key] = by_type.get(type_key, 0) + 1

        table_key = change.table
        by_table[table_key] = by_table.get(table_key, 0) + 1

    return DiffStats(
        total=len(changes),
        by_type=by_type,
        by_table=by_table,
        tables_affected=len(by_table),
    )
