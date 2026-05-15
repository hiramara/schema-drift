"""Tests for schema_drift.tracer."""

from __future__ import annotations

import pytest

from schema_drift.snapshot import ColumnSchema, DatabaseSnapshot, TableSchema
from schema_drift.tracer import TraceEntry, TraceResult, trace_column, trace_table


def _col(name: str, col_type: str = "TEXT", nullable: bool = True) -> ColumnSchema:
    return ColumnSchema(name=name, col_type=col_type, nullable=nullable)


def _snap(sid: str, tables: dict) -> DatabaseSnapshot:
    return DatabaseSnapshot(snapshot_id=sid, tables=tables)


_users_v1 = TableSchema(
    name="users",
    columns={"id": _col("id", "INT", False), "name": _col("name")},
    indexes={},
)
_users_v2 = TableSchema(
    name="users",
    columns={"id": _col("id", "INT", False), "name": _col("name"), "email": _col("email")},
    indexes={},
)

SNAP1 = _snap("snap-1", {"users": _users_v1})
SNAP2 = _snap("snap-2", {"users": _users_v2})
SNAP3 = _snap("snap-3", {})


class TestTraceTable:
    def test_table_present_in_all_snapshots(self):
        result = trace_table([SNAP1, SNAP2], "users")
        assert all(e.exists for e in result.entries)

    def test_table_absent_in_last_snapshot(self):
        result = trace_table([SNAP1, SNAP2, SNAP3], "users")
        assert result.entries[-1].exists is False

    def test_entry_count_matches_snapshots(self):
        result = trace_table([SNAP1, SNAP2, SNAP3], "users")
        assert len(result.entries) == 3

    def test_snapshot_ids_preserved(self):
        result = trace_table([SNAP1, SNAP2], "users")
        assert [e.snapshot_id for e in result.entries] == ["snap-1", "snap-2"]

    def test_detail_contains_column_count(self):
        result = trace_table([SNAP1], "users")
        assert result.entries[0].detail["columns"] == 2

    def test_missing_table_detail_columns_zero(self):
        result = trace_table([SNAP3], "users")
        assert result.entries[0].detail["columns"] == 0

    def test_to_dict_structure(self):
        result = trace_table([SNAP1], "users")
        d = result.to_dict()
        assert d["table"] == "users"
        assert d["column"] is None
        assert isinstance(d["entries"], list)


class TestTraceColumn:
    def test_column_present_in_both(self):
        result = trace_column([SNAP1, SNAP2], "users", "name")
        assert all(e.exists for e in result.entries)

    def test_new_column_absent_then_present(self):
        result = trace_column([SNAP1, SNAP2], "users", "email")
        assert result.entries[0].exists is False
        assert result.entries[1].exists is True

    def test_detail_type_recorded(self):
        result = trace_column([SNAP1], "users", "id")
        assert result.entries[0].detail["type"] == "INT"

    def test_detail_nullable_recorded(self):
        result = trace_column([SNAP1], "users", "id")
        assert result.entries[0].detail["nullable"] is False

    def test_missing_column_detail_none(self):
        result = trace_column([SNAP1], "users", "email")
        assert result.entries[0].detail["type"] is None

    def test_column_field_set_in_result(self):
        result = trace_column([SNAP1], "users", "name")
        assert result.column == "name"

    def test_to_dict_has_column_key(self):
        result = trace_column([SNAP1], "users", "name")
        assert result.to_dict()["column"] == "name"
