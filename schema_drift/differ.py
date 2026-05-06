"""Schema differ module for comparing two snapshots and producing a structured diff."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from schema_drift.snapshot import SchemaSnapshot, TableSchema, ColumnSchema


class ChangeType(str, Enum):
    TABLE_ADDED = "table_added"
    TABLE_REMOVED = "table_removed"
    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"
    COLUMN_MODIFIED = "column_modified"
    INDEX_ADDED = "index_added"
    INDEX_REMOVED = "index_removed"


@dataclass
class SchemaChange:
    change_type: ChangeType
    table: str
    object_name: str
    before: dict = field(default_factory=dict)
    after: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "change_type": self.change_type.value,
            "table": self.table,
            "object_name": self.object_name,
            "before": self.before,
            "after": self.after,
        }


def diff_columns(table_name: str, old: TableSchema, new: TableSchema) -> List[SchemaChange]:
    changes: List[SchemaChange] = []
    old_cols = {c.name: c for c in old.columns}
    new_cols = {c.name: c for c in new.columns}

    for name in old_cols.keys() - new_cols.keys():
        changes.append(SchemaChange(
            change_type=ChangeType.COLUMN_REMOVED,
            table=table_name,
            object_name=name,
            before=old_cols[name].to_dict(),
        ))

    for name in new_cols.keys() - old_cols.keys():
        changes.append(SchemaChange(
            change_type=ChangeType.COLUMN_ADDED,
            table=table_name,
            object_name=name,
            after=new_cols[name].to_dict(),
        ))

    for name in old_cols.keys() & new_cols.keys():
        old_d, new_d = old_cols[name].to_dict(), new_cols[name].to_dict()
        if old_d != new_d:
            changes.append(SchemaChange(
                change_type=ChangeType.COLUMN_MODIFIED,
                table=table_name,
                object_name=name,
                before=old_d,
                after=new_d,
            ))
    return changes


def diff_indexes(table_name: str, old: TableSchema, new: TableSchema) -> List[SchemaChange]:
    changes: List[SchemaChange] = []
    old_idx, new_idx = set(old.indexes), set(new.indexes)
    for idx in old_idx - new_idx:
        changes.append(SchemaChange(ChangeType.INDEX_REMOVED, table_name, idx, before={"index": idx}))
    for idx in new_idx - old_idx:
        changes.append(SchemaChange(ChangeType.INDEX_ADDED, table_name, idx, after={"index": idx}))
    return changes


def diff_snapshots(old: SchemaSnapshot, new: SchemaSnapshot) -> List[SchemaChange]:
    changes: List[SchemaChange] = []
    old_tables, new_tables = old.tables, new.tables

    for name in old_tables.keys() - new_tables.keys():
        changes.append(SchemaChange(ChangeType.TABLE_REMOVED, name, name, before=old_tables[name].to_dict()))

    for name in new_tables.keys() - old_tables.keys():
        changes.append(SchemaChange(ChangeType.TABLE_ADDED, name, name, after=new_tables[name].to_dict()))

    for name in old_tables.keys() & new_tables.keys():
        changes.extend(diff_columns(name, old_tables[name], new_tables[name]))
        changes.extend(diff_indexes(name, old_tables[name], new_tables[name]))

    return changes
