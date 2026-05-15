"""Tests for schema_drift.differ_stats."""
from __future__ import annotations

import pytest

from schema_drift.differ import SchemaChange, ChangeType
from schema_drift.differ_stats import compute_diff_stats, DiffStats


def _change(
    table: str = "users",
    change_type: ChangeType = ChangeType.COLUMN_ADDED,
    column: str = "email",
) -> SchemaChange:
    return SchemaChange(change_type=change_type, table=table, column=column, detail="")


class TestComputeDiffStats:
    def test_empty_list_returns_zeros(self):
        stats = compute_diff_stats([])
        assert stats.total == 0
        assert stats.tables_affected == 0
        assert stats.by_type == {}
        assert stats.by_table == {}

    def test_single_change_total_is_one(self):
        stats = compute_diff_stats([_change()])
        assert stats.total == 1

    def test_single_change_table_counted(self):
        stats = compute_diff_stats([_change(table="orders")])
        assert stats.by_table == {"orders": 1}
        assert stats.tables_affected == 1

    def test_two_changes_same_table(self):
        changes = [_change(table="users"), _change(table="users", column="name")]
        stats = compute_diff_stats(changes)
        assert stats.tables_affected == 1
        assert stats.by_table["users"] == 2

    def test_two_changes_different_tables(self):
        changes = [_change(table="users"), _change(table="orders")]
        stats = compute_diff_stats(changes)
        assert stats.tables_affected == 2

    def test_by_type_counts_correctly(self):
        changes = [
            _change(change_type=ChangeType.COLUMN_ADDED),
            _change(change_type=ChangeType.COLUMN_ADDED, column="age"),
            _change(change_type=ChangeType.COLUMN_REMOVED, column="old"),
        ]
        stats = compute_diff_stats(changes)
        assert stats.by_type[ChangeType.COLUMN_ADDED.value] == 2
        assert stats.by_type[ChangeType.COLUMN_REMOVED.value] == 1

    def test_to_dict_has_required_keys(self):
        stats = compute_diff_stats([_change()])
        d = stats.to_dict()
        assert set(d.keys()) == {"total", "by_type", "by_table", "tables_affected"}

    def test_to_dict_values_match_attributes(self):
        stats = compute_diff_stats([_change(table="users")])
        d = stats.to_dict()
        assert d["total"] == stats.total
        assert d["tables_affected"] == stats.tables_affected
