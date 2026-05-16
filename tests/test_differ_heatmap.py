"""Tests for schema_drift.differ_heatmap."""

from __future__ import annotations

import pytest

from schema_drift.differ import ChangeType, SchemaChange
from schema_drift.differ_heatmap import build_heatmap, DriftHeatmap


def _change(
    table: str = "users",
    change_type: ChangeType = ChangeType.COLUMN_ADDED,
    column: str = "id",
) -> SchemaChange:
    return SchemaChange(
        table=table,
        change_type=change_type,
        column=column,
        detail="",
    )


class TestBuildHeatmap:
    def test_empty_change_sets_returns_empty_heatmap(self):
        heatmap = build_heatmap([])
        assert heatmap.cells == []

    def test_empty_inner_list_returns_empty_heatmap(self):
        heatmap = build_heatmap([[]])
        assert heatmap.cells == []

    def test_single_change_creates_one_cell(self):
        heatmap = build_heatmap([[_change("orders")]])
        assert len(heatmap.cells) == 1
        assert heatmap.cells[0].table == "orders"

    def test_total_changes_counted_correctly(self):
        changes = [
            _change("users", ChangeType.COLUMN_ADDED),
            _change("users", ChangeType.COLUMN_REMOVED),
        ]
        heatmap = build_heatmap([changes])
        assert heatmap.total_changes() == 2

    def test_by_type_breakdown_is_accurate(self):
        changes = [
            _change("users", ChangeType.COLUMN_ADDED),
            _change("users", ChangeType.COLUMN_ADDED),
            _change("users", ChangeType.COLUMN_REMOVED),
        ]
        heatmap = build_heatmap([changes])
        cell = heatmap.cells[0]
        assert cell.by_type[ChangeType.COLUMN_ADDED.value] == 2
        assert cell.by_type[ChangeType.COLUMN_REMOVED.value] == 1

    def test_multiple_tables_create_multiple_cells(self):
        changes = [
            _change("users"),
            _change("orders"),
            _change("products"),
        ]
        heatmap = build_heatmap([changes])
        tables = {c.table for c in heatmap.cells}
        assert tables == {"users", "orders", "products"}

    def test_changes_across_multiple_diffs_accumulated(self):
        diff1 = [_change("users")]
        diff2 = [_change("users"), _change("orders")]
        heatmap = build_heatmap([diff1, diff2])
        by_table = {c.table: c.total_changes for c in heatmap.cells}
        assert by_table["users"] == 2
        assert by_table["orders"] == 1

    def test_hottest_table_is_most_changed(self):
        diff1 = [_change("users"), _change("users"), _change("orders")]
        heatmap = build_heatmap([diff1])
        assert heatmap.hottest_table() == "users"

    def test_hottest_table_none_when_empty(self):
        heatmap = build_heatmap([])
        assert heatmap.hottest_table() is None

    def test_sorted_cells_descending(self):
        changes = [
            _change("a"),
            _change("b"),
            _change("b"),
            _change("c"),
            _change("c"),
            _change("c"),
        ]
        heatmap = build_heatmap([changes])
        totals = [c.total_changes for c in heatmap.sorted_cells()]
        assert totals == sorted(totals, reverse=True)

    def test_to_dict_contains_required_keys(self):
        heatmap = build_heatmap([[_change()]])
        d = heatmap.to_dict()
        assert "total_changes" in d
        assert "hottest_table" in d
        assert "cells" in d

    def test_cell_to_dict_shape(self):
        heatmap = build_heatmap([[_change("users", ChangeType.COLUMN_ADDED)]])
        cell_dict = heatmap.cells[0].to_dict()
        assert cell_dict["table"] == "users"
        assert cell_dict["total_changes"] == 1
        assert isinstance(cell_dict["by_type"], dict)
