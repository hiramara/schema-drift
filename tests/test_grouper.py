"""Tests for schema_drift.grouper."""

from __future__ import annotations

import pytest

from schema_drift.differ import ChangeType, SchemaChange
from schema_drift.grouper import (
    ChangeGroup,
    group_by_change_type,
    group_by_severity,
    group_by_table,
    groups_to_dict,
)


def _change(
    table: str = "users",
    change_type: ChangeType = ChangeType.COLUMN_ADDED,
    column: str | None = "email",
) -> SchemaChange:
    return SchemaChange(
        table=table,
        change_type=change_type,
        column=column,
        detail="",
    )


class TestGroupByTable:
    def test_empty_returns_empty_dict(self):
        assert group_by_table([]) == {}

    def test_single_change_creates_one_group(self):
        result = group_by_table([_change(table="orders")])
        assert "orders" in result
        assert len(result["orders"].changes) == 1

    def test_two_tables_create_two_groups(self):
        changes = [_change(table="users"), _change(table="orders")]
        result = group_by_table(changes)
        assert set(result.keys()) == {"users", "orders"}

    def test_same_table_changes_are_merged(self):
        changes = [_change(table="users"), _change(table="users", column="name")]
        result = group_by_table(changes)
        assert len(result) == 1
        assert len(result["users"].changes) == 2

    def test_group_key_matches_table_name(self):
        result = group_by_table([_change(table="products")])
        assert result["products"].key == "products"


class TestGroupByChangeType:
    def test_empty_returns_empty_dict(self):
        assert group_by_change_type([]) == {}

    def test_groups_on_change_type_value(self):
        changes = [
            _change(change_type=ChangeType.COLUMN_ADDED),
            _change(change_type=ChangeType.COLUMN_REMOVED),
        ]
        result = group_by_change_type(changes)
        assert ChangeType.COLUMN_ADDED.value in result
        assert ChangeType.COLUMN_REMOVED.value in result

    def test_same_type_merged(self):
        changes = [
            _change(change_type=ChangeType.COLUMN_ADDED, column="a"),
            _change(change_type=ChangeType.COLUMN_ADDED, column="b"),
        ]
        result = group_by_change_type(changes)
        assert len(result) == 1
        key = ChangeType.COLUMN_ADDED.value
        assert len(result[key].changes) == 2


class TestGroupBySeverity:
    def test_empty_returns_empty_dict(self):
        assert group_by_severity([]) == {}

    def test_column_removed_is_critical(self):
        result = group_by_severity([_change(change_type=ChangeType.COLUMN_REMOVED)])
        assert "critical" in result

    def test_column_added_is_info(self):
        result = group_by_severity([_change(change_type=ChangeType.COLUMN_ADDED)])
        assert "info" in result

    def test_mixed_severities_produce_multiple_groups(self):
        changes = [
            _change(change_type=ChangeType.COLUMN_ADDED),
            _change(change_type=ChangeType.COLUMN_REMOVED),
        ]
        result = group_by_severity(changes)
        assert len(result) >= 2


class TestGroupsToDict:
    def test_serialises_key_and_count(self):
        groups = group_by_table([_change(table="users")])
        d = groups_to_dict(groups)
        assert d["users"]["key"] == "users"
        assert d["users"]["count"] == 1

    def test_changes_list_present(self):
        groups = group_by_table([_change(table="users")])
        d = groups_to_dict(groups)
        assert isinstance(d["users"]["changes"], list)
        assert len(d["users"]["changes"]) == 1
