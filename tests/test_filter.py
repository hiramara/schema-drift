"""Tests for schema_drift.filter."""

from __future__ import annotations

import pytest

from schema_drift.differ import SchemaChange, ChangeType
from schema_drift.filter import FilterConfig, apply_filter


def _change(
    table: str = "users",
    change_type: ChangeType = ChangeType.COLUMN_ADDED,
    object_name: str = "email",
) -> SchemaChange:
    return SchemaChange(
        table=table,
        change_type=change_type,
        object_name=object_name,
        detail="",
    )


class TestFilterConfigRoundTrip:
    def test_empty_config_round_trips(self):
        cfg = FilterConfig()
        restored = FilterConfig.from_dict(cfg.to_dict())
        assert restored.tables is None
        assert restored.change_types is None
        assert restored.min_severity is None
        assert restored.exclude_tables == set()

    def test_tables_round_trips(self):
        cfg = FilterConfig(tables={"users", "orders"})
        restored = FilterConfig.from_dict(cfg.to_dict())
        assert restored.tables == {"users", "orders"}

    def test_change_types_round_trips(self):
        cfg = FilterConfig(change_types={ChangeType.COLUMN_ADDED, ChangeType.COLUMN_REMOVED})
        restored = FilterConfig.from_dict(cfg.to_dict())
        assert restored.change_types == {ChangeType.COLUMN_ADDED, ChangeType.COLUMN_REMOVED}


class TestApplyFilter:
    def test_no_filter_returns_all(self):
        changes = [_change("users"), _change("orders")]
        cfg = FilterConfig()
        assert apply_filter(changes, cfg) == changes

    def test_table_filter_keeps_matching(self):
        changes = [_change("users"), _change("orders")]
        cfg = FilterConfig(tables={"users"})
        result = apply_filter(changes, cfg)
        assert len(result) == 1
        assert result[0].table == "users"

    def test_exclude_tables_removes_matching(self):
        changes = [_change("users"), _change("orders")]
        cfg = FilterConfig(exclude_tables={"orders"})
        result = apply_filter(changes, cfg)
        assert all(c.table != "orders" for c in result)

    def test_change_type_filter(self):
        changes = [
            _change(change_type=ChangeType.COLUMN_ADDED),
            _change(change_type=ChangeType.COLUMN_REMOVED),
        ]
        cfg = FilterConfig(change_types={ChangeType.COLUMN_ADDED})
        result = apply_filter(changes, cfg)
        assert len(result) == 1
        assert result[0].change_type == ChangeType.COLUMN_ADDED

    def test_min_severity_critical_filters_low(self):
        changes = [
            _change(change_type=ChangeType.COLUMN_ADDED),    # low
            _change(change_type=ChangeType.COLUMN_REMOVED),  # critical
        ]
        cfg = FilterConfig(min_severity="critical")
        result = apply_filter(changes, cfg)
        assert len(result) == 1
        assert result[0].change_type == ChangeType.COLUMN_REMOVED

    def test_empty_changes_returns_empty(self):
        cfg = FilterConfig(tables={"users"})
        assert apply_filter([], cfg) == []

    def test_exclude_and_table_filter_combined(self):
        changes = [
            _change("users"),
            _change("orders"),
            _change("products"),
        ]
        cfg = FilterConfig(tables={"users", "orders"}, exclude_tables={"orders"})
        result = apply_filter(changes, cfg)
        assert len(result) == 1
        assert result[0].table == "users"
