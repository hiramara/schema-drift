"""Tests for schema_drift.differ_rollup."""
import pytest

from schema_drift.differ import ChangeType, SchemaChange
from schema_drift.differ_rollup import DiffRollup, TableRollup, rollup_changes


def _change(
    table: str = "users",
    change_type: ChangeType = ChangeType.COLUMN_ADDED,
    column: str = "email",
) -> SchemaChange:
    return SchemaChange(
        change_type=change_type,
        table=table,
        object_name=column,
        detail="",
    )


class TestRollupChanges:
    def test_empty_list_returns_zero_totals(self):
        result = rollup_changes([])
        assert result.total_changes == 0
        assert result.tables_affected == 0
        assert result.by_type == {}
        assert result.by_table == {}

    def test_single_change_total_is_one(self):
        result = rollup_changes([_change()])
        assert result.total_changes == 1

    def test_single_change_tables_affected_is_one(self):
        result = rollup_changes([_change()])
        assert result.tables_affected == 1

    def test_single_change_by_type_counted(self):
        result = rollup_changes([_change(change_type=ChangeType.COLUMN_ADDED)])
        assert result.by_type.get("column_added") == 1

    def test_two_changes_same_table(self):
        changes = [
            _change(table="users", change_type=ChangeType.COLUMN_ADDED, column="a"),
            _change(table="users", change_type=ChangeType.COLUMN_REMOVED, column="b"),
        ]
        result = rollup_changes(changes)
        assert result.tables_affected == 1
        assert result.total_changes == 2
        assert result.by_table["users"].total == 2

    def test_two_changes_different_tables(self):
        changes = [
            _change(table="users"),
            _change(table="orders"),
        ]
        result = rollup_changes(changes)
        assert result.tables_affected == 2

    def test_by_type_accumulates_across_tables(self):
        changes = [
            _change(table="users", change_type=ChangeType.COLUMN_ADDED),
            _change(table="orders", change_type=ChangeType.COLUMN_ADDED),
        ]
        result = rollup_changes(changes)
        assert result.by_type["column_added"] == 2

    def test_table_rollup_by_type_correct(self):
        changes = [
            _change(table="users", change_type=ChangeType.COLUMN_ADDED, column="x"),
            _change(table="users", change_type=ChangeType.COLUMN_ADDED, column="y"),
            _change(table="users", change_type=ChangeType.COLUMN_REMOVED, column="z"),
        ]
        result = rollup_changes(changes)
        tr = result.by_table["users"]
        assert tr.by_type["column_added"] == 2
        assert tr.by_type["column_removed"] == 1

    def test_to_dict_structure(self):
        result = rollup_changes([_change()])
        d = result.to_dict()
        assert "total_changes" in d
        assert "tables_affected" in d
        assert "by_type" in d
        assert "by_table" in d

    def test_table_rollup_to_dict(self):
        result = rollup_changes([_change(table="users")])
        td = result.to_dict()["by_table"]["users"]
        assert td["table"] == "users"
        assert td["total"] == 1
        assert isinstance(td["by_type"], dict)
