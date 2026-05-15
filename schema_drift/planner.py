"""Migration planner: generates SQL migration hints from a diff."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from schema_drift.differ import SchemaChange, ChangeType


@dataclass
class MigrationStep:
    order: int
    change_type: str
    table: str
    description: str
    sql_hint: str

    def to_dict(self) -> dict:
        return {
            "order": self.order,
            "change_type": self.change_type,
            "table": self.table,
            "description": self.description,
            "sql_hint": self.sql_hint,
        }


@dataclass
class MigrationPlan:
    steps: List[MigrationStep] = field(default_factory=list)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def to_dict(self) -> dict:
        return {
            "step_count": self.step_count,
            "steps": [s.to_dict() for s in self.steps],
        }


_PRIORITY = {
    ChangeType.COLUMN_REMOVED: 0,
    ChangeType.INDEX_REMOVED: 1,
    ChangeType.TABLE_REMOVED: 2,
    ChangeType.COLUMN_ADDED: 3,
    ChangeType.COLUMN_MODIFIED: 4,
    ChangeType.INDEX_ADDED: 5,
    ChangeType.TABLE_ADDED: 6,
}


def _sql_hint(change: SchemaChange) -> str:
    t = change.table
    col = change.column or ""
    ct = change.change_type

    if ct == ChangeType.COLUMN_ADDED:
        col_type = (change.new_value or {}).get("type", "TEXT") if isinstance(change.new_value, dict) else "TEXT"
        return f"ALTER TABLE {t} ADD COLUMN {col} {col_type};"
    if ct == ChangeType.COLUMN_REMOVED:
        return f"ALTER TABLE {t} DROP COLUMN {col};"
    if ct == ChangeType.COLUMN_MODIFIED:
        new_type = (change.new_value or {}).get("type", "TEXT") if isinstance(change.new_value, dict) else "TEXT"
        return f"-- ALTER TABLE {t} MODIFY COLUMN {col} {new_type};  -- verify dialect"
    if ct == ChangeType.TABLE_ADDED:
        return f"CREATE TABLE {t} ( /* define columns */ );"
    if ct == ChangeType.TABLE_REMOVED:
        return f"DROP TABLE {t};"
    if ct == ChangeType.INDEX_ADDED:
        return f"-- CREATE INDEX on {t} ({col or '?'});"
    if ct == ChangeType.INDEX_REMOVED:
        return f"-- DROP INDEX on {t} ({col or '?'});"
    return f"-- no hint for {ct.value} on {t}"


def plan_migration(changes: List[SchemaChange]) -> MigrationPlan:
    """Convert a list of SchemaChange objects into an ordered MigrationPlan."""
    sorted_changes = sorted(
        changes,
        key=lambda c: _PRIORITY.get(c.change_type, 99),
    )
    steps = [
        MigrationStep(
            order=i + 1,
            change_type=c.change_type.value,
            table=c.table,
            description=c.description,
            sql_hint=_sql_hint(c),
        )
        for i, c in enumerate(sorted_changes)
    ]
    return MigrationPlan(steps=steps)
