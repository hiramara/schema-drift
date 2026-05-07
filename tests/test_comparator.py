"""Tests for schema_drift.comparator."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from schema_drift.comparator import (
    ComparisonResult,
    compare_latest_two,
    compare_snapshots,
)
from schema_drift.differ import ChangeType
from schema_drift.snapshot import ColumnSchema, DatabaseSnapshot, TableSchema
from schema_drift.storage import save_snapshot


def _col(name: str, col_type: str = "TEXT", nullable: bool = True) -> ColumnSchema:
    return ColumnSchema(name=name, col_type=col_type, nullable=nullable, default=None)


def _snap(snap_id: str, tables: dict) -> DatabaseSnapshot:
    return DatabaseSnapshot(snapshot_id=snap_id, tables=tables)


def _users_table(*col_names: str) -> TableSchema:
    cols = {n: _col(n) for n in col_names}
    return TableSchema(name="users", columns=cols, indexes={})


class TestCompareSnapshots:
    def test_no_changes(self):
        snap = _snap("a", {"users": _users_table("id", "email")})
        result = compare_snapshots(snap, snap)
        assert not result.has_changes
        assert result.change_count == 0

    def test_added_column_detected(self):
        old = _snap("a", {"users": _users_table("id")})
        new = _snap("b", {"users": _users_table("id", "email")})
        result = compare_snapshots(old, new)
        assert result.has_changes
        assert any(
            c.change_type == ChangeType.COLUMN_ADDED and c.object_name == "email"
            for c in result.changes
        )

    def test_removed_column_detected(self):
        old = _snap("a", {"users": _users_table("id", "email")})
        new = _snap("b", {"users": _users_table("id")})
        result = compare_snapshots(old, new)
        assert result.has_changes
        assert any(c.change_type == ChangeType.COLUMN_REMOVED for c in result.changes)

    def test_result_references_correct_snapshots(self):
        old = _snap("snap-1", {})
        new = _snap("snap-2", {})
        result = compare_snapshots(old, new)
        assert result.old_snapshot.snapshot_id == "snap-1"
        assert result.new_snapshot.snapshot_id == "snap-2"

    def test_to_dict_structure(self):
        old = _snap("x", {})
        new = _snap("y", {})
        d = compare_snapshots(old, new).to_dict()
        assert d["old_snapshot_id"] == "x"
        assert d["new_snapshot_id"] == "y"
        assert "changes" in d
        assert isinstance(d["changes"], list)


class TestCompareLatestTwo:
    def test_returns_none_when_fewer_than_two_snapshots(self, tmp_path):
        result = compare_latest_two(str(tmp_path))
        assert result is None

    def test_returns_none_with_single_snapshot(self, tmp_path):
        snap = _snap("only", {})
        save_snapshot(str(tmp_path), snap)
        assert compare_latest_two(str(tmp_path)) is None

    def test_compares_two_snapshots(self, tmp_path):
        old = _snap("first", {"users": _users_table("id")})
        new = _snap("second", {"users": _users_table("id", "email")})
        save_snapshot(str(tmp_path), old)
        save_snapshot(str(tmp_path), new)
        result = compare_latest_two(str(tmp_path))
        assert result is not None
        assert result.has_changes
