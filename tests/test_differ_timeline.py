"""Tests for schema_drift.differ_timeline."""

from __future__ import annotations

import pytest

from schema_drift.snapshot import DatabaseSnapshot, TableSchema, ColumnSchema
from schema_drift.differ import ChangeType
from schema_drift.differ_timeline import build_timeline, SchemaTimeline, TimelineEntry


def _col(name: str, col_type: str = "TEXT", nullable: bool = True) -> ColumnSchema:
    return ColumnSchema(name=name, col_type=col_type, nullable=nullable, default=None)


def _snap(
    snap_id: str,
    tables: dict[str, list[ColumnSchema]] | None = None,
) -> DatabaseSnapshot:
    table_schemas = {}
    for tname, cols in (tables or {}).items():
        table_schemas[tname] = TableSchema(name=tname, columns=cols, indexes=[])
    return DatabaseSnapshot(snapshot_id=snap_id, tables=table_schemas)


class TestBuildTimeline:
    def test_raises_with_single_snapshot(self):
        snap = _snap("s1", {"users": [_col("id")]})
        with pytest.raises(ValueError, match="two snapshots"):
            build_timeline([snap])

    def test_raises_with_empty_list(self):
        with pytest.raises(ValueError):
            build_timeline([])

    def test_two_identical_snapshots_no_changes(self):
        snap1 = _snap("s1", {"users": [_col("id")]})
        snap2 = _snap("s2", {"users": [_col("id")]})
        timeline = build_timeline([snap1, snap2])
        assert isinstance(timeline, SchemaTimeline)
        assert len(timeline.entries) == 1
        assert timeline.total_changes == 0

    def test_entry_ids_are_correct(self):
        snap1 = _snap("alpha", {})
        snap2 = _snap("beta", {})
        timeline = build_timeline([snap1, snap2])
        entry = timeline.entries[0]
        assert entry.from_id == "alpha"
        assert entry.to_id == "beta"

    def test_detects_added_column(self):
        snap1 = _snap("s1", {"orders": [_col("id")]})
        snap2 = _snap("s2", {"orders": [_col("id"), _col("total")]})
        timeline = build_timeline([snap1, snap2])
        assert timeline.total_changes == 1
        change = timeline.entries[0].changes[0]
        assert change.change_type == ChangeType.COLUMN_ADDED
        assert change.column == "total"

    def test_three_snapshots_two_entries(self):
        snap1 = _snap("s1", {"t": [_col("a")]})
        snap2 = _snap("s2", {"t": [_col("a"), _col("b")]})
        snap3 = _snap("s3", {"t": [_col("a"), _col("b"), _col("c")]})
        timeline = build_timeline([snap1, snap2, snap3])
        assert len(timeline.entries) == 2
        assert timeline.total_changes == 2

    def test_snapshot_ids_property(self):
        snap1 = _snap("s1", {})
        snap2 = _snap("s2", {})
        snap3 = _snap("s3", {})
        timeline = build_timeline([snap1, snap2, snap3])
        assert timeline.snapshot_ids == ["s1", "s2", "s3"]

    def test_changes_for_table_filters_correctly(self):
        snap1 = _snap("s1", {"users": [_col("id")], "orders": [_col("id")]})
        snap2 = _snap(
            "s2",
            {"users": [_col("id"), _col("email")], "orders": [_col("id")]},
        )
        timeline = build_timeline([snap1, snap2])
        user_changes = timeline.changes_for_table("users")
        order_changes = timeline.changes_for_table("orders")
        assert len(user_changes) == 1
        assert len(order_changes) == 0

    def test_to_dict_structure(self):
        snap1 = _snap("s1", {"t": [_col("id")]})
        snap2 = _snap("s2", {"t": [_col("id"), _col("name")]})
        d = build_timeline([snap1, snap2]).to_dict()
        assert "snapshot_ids" in d
        assert "total_changes" in d
        assert "entries" in d
        assert d["total_changes"] == 1
        assert d["snapshot_ids"] == ["s1", "s2"]

    def test_entry_to_dict_has_change_count(self):
        snap1 = _snap("s1", {"t": [_col("id")]})
        snap2 = _snap("s2", {"t": [_col("id"), _col("x")]})
        timeline = build_timeline([snap1, snap2])
        entry_dict = timeline.entries[0].to_dict()
        assert entry_dict["change_count"] == 1
        assert entry_dict["from_id"] == "s1"
        assert entry_dict["to_id"] == "s2"
