"""Tests for the snapshot and differ modules."""

import json
import pytest
from datetime import datetime, timezone

from schema_drift.snapshot import ColumnSchema, TableSchema, SchemaSnapshot
from schema_drift.differ import ChangeType, diff_snapshots


def make_snapshot(database: str, tables: dict) -> SchemaSnapshot:
    return SchemaSnapshot(
        captured_at=datetime.now(timezone.utc),
        database=database,
        tables=tables,
    )


def users_table(extra_col: bool = False, nullable_email: bool = False) -> TableSchema:
    cols = [
        ColumnSchema("id", "integer", False, primary_key=True),
        ColumnSchema("email", "varchar(255)", nullable_email),
    ]
    if extra_col:
        cols.append(ColumnSchema("created_at", "timestamp", True))
    return TableSchema(name="users", columns=cols, indexes=["idx_users_email"])


class TestSchemaSnapshot:
    def test_round_trip_json(self):
        snap = make_snapshot("mydb", {"users": users_table()})
        restored = SchemaSnapshot.from_json(snap.to_json())
        assert restored.database == snap.database
        assert list(restored.tables.keys()) == list(snap.tables.keys())
        assert restored.tables["users"].columns[0].name == "id"

    def test_column_serialization(self):
        col = ColumnSchema("id", "integer", False, primary_key=True)
        assert col.to_dict()["primary_key"] is True
        restored = ColumnSchema.from_dict(col.to_dict())
        assert restored == col


class TestDiffSnapshots:
    def test_no_changes(self):
        snap = make_snapshot("db", {"users": users_table()})
        changes = diff_snapshots(snap, snap)
        assert changes == []

    def test_table_added(self):
        old = make_snapshot("db", {})
        new = make_snapshot("db", {"users": users_table()})
        changes = diff_snapshots(old, new)
        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.TABLE_ADDED
        assert changes[0].table == "users"

    def test_table_removed(self):
        old = make_snapshot("db", {"users": users_table()})
        new = make_snapshot("db", {})
        changes = diff_snapshots(old, new)
        assert any(c.change_type == ChangeType.TABLE_REMOVED for c in changes)

    def test_column_added(self):
        old = make_snapshot("db", {"users": users_table(extra_col=False)})
        new = make_snapshot("db", {"users": users_table(extra_col=True)})
        changes = diff_snapshots(old, new)
        assert any(c.change_type == ChangeType.COLUMN_ADDED and c.object_name == "created_at" for c in changes)

    def test_column_modified(self):
        old = make_snapshot("db", {"users": users_table(nullable_email=False)})
        new = make_snapshot("db", {"users": users_table(nullable_email=True)})
        changes = diff_snapshots(old, new)
        modified = [c for c in changes if c.change_type == ChangeType.COLUMN_MODIFIED]
        assert len(modified) == 1
        assert modified[0].object_name == "email"
        assert modified[0].before["nullable"] is False
        assert modified[0].after["nullable"] is True

    def test_index_removed(self):
        old_table = users_table()
        new_table = TableSchema(name="users", columns=old_table.columns, indexes=[])
        old = make_snapshot("db", {"users": old_table})
        new = make_snapshot("db", {"users": new_table})
        changes = diff_snapshots(old, new)
        assert any(c.change_type == ChangeType.INDEX_REMOVED for c in changes)

    def test_change_to_dict(self):
        old = make_snapshot("db", {})
        new = make_snapshot("db", {"users": users_table()})
        changes = diff_snapshots(old, new)
        d = changes[0].to_dict()
        assert d["change_type"] == "table_added"
        assert "table" in d
