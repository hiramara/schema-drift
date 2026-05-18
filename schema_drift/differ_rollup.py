"""Rollup aggregator: collapses a list of SchemaChange objects into
per-table and per-type summary counts suitable for dashboards."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from schema_drift.differ import SchemaChange


@dataclass
class TableRollup:
    table: str
    total: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "total": self.total,
            "by_type": dict(self.by_type),
        }


@dataclass
class DiffRollup:
    total_changes: int = 0
    tables_affected: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_table: Dict[str, TableRollup] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "total_changes": self.total_changes,
            "tables_affected": self.tables_affected,
            "by_type": dict(self.by_type),
            "by_table": {t: r.to_dict() for t, r in self.by_table.items()},
        }


def rollup_changes(changes: List[SchemaChange]) -> DiffRollup:
    """Aggregate *changes* into a :class:`DiffRollup`."""
    result = DiffRollup()

    for change in changes:
        type_key = change.change_type.value
        table = change.table

        result.total_changes += 1
        result.by_type[type_key] = result.by_type.get(type_key, 0) + 1

        if table not in result.by_table:
            result.by_table[table] = TableRollup(table=table)
        tr = result.by_table[table]
        tr.total += 1
        tr.by_type[type_key] = tr.by_type.get(type_key, 0) + 1

    result.tables_affected = len(result.by_table)
    return result
