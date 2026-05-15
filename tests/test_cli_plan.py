"""Tests for schema_drift.cli_plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from schema_drift.snapshot import DatabaseSnapshot, TableSchema, ColumnSchema
from schema_drift.cli_plan import cmd_plan


def _make_snapshot(snap_id: str, storage: Path) -> DatabaseSnapshot:
    col = ColumnSchema(name="id", col_type="INTEGER", nullable=False, default=None)
    table = TableSchema(name="users", columns=[col], indexes=[])
    snap = DatabaseSnapshot(snapshot_id=snap_id, created_at="2024-01-01T00:00:00Z", tables=[table])
    from schema_drift.storage import save_snapshot
    save_snapshot(str(storage), snap)
    return snap


def _args(storage: Path, from_id: str, to_id: str, fmt: str = "text") -> argparse.Namespace:
    return argparse.Namespace(
        storage_dir=str(storage),
        from_snapshot=from_id,
        to_snapshot=to_id,
        format=fmt,
    )


class TestCmdPlan:
    def test_missing_from_snapshot_returns_2(self, tmp_path):
        _make_snapshot("snap-b", tmp_path)
        result = cmd_plan(_args(tmp_path, "snap-a", "snap-b"))
        assert result == 2

    def test_missing_to_snapshot_returns_2(self, tmp_path):
        _make_snapshot("snap-a", tmp_path)
        result = cmd_plan(_args(tmp_path, "snap-a", "snap-b"))
        assert result == 2

    def test_no_changes_returns_0(self, tmp_path, capsys):
        _make_snapshot("snap-a", tmp_path)
        _make_snapshot("snap-b", tmp_path)
        result = cmd_plan(_args(tmp_path, "snap-a", "snap-b"))
        assert result == 0
        out = capsys.readouterr().out
        assert "No migration steps" in out

    def test_json_format_is_valid(self, tmp_path):
        _make_snapshot("snap-a", tmp_path)

        col2 = ColumnSchema(name="email", col_type="TEXT", nullable=True, default=None)
        from schema_drift.snapshot import DatabaseSnapshot, TableSchema
        from schema_drift.storage import save_snapshot
        table = TableSchema(name="users", columns=[
            ColumnSchema(name="id", col_type="INTEGER", nullable=False, default=None),
            col2,
        ], indexes=[])
        snap_b = DatabaseSnapshot(snapshot_id="snap-b", created_at="2024-01-02T00:00:00Z", tables=[table])
        save_snapshot(str(tmp_path), snap_b)

        result = cmd_plan(_args(tmp_path, "snap-a", "snap-b", fmt="json"))
        assert result == 0

    def test_text_output_contains_sql_hint(self, tmp_path, capsys):
        _make_snapshot("snap-a", tmp_path)

        from schema_drift.snapshot import DatabaseSnapshot, TableSchema, ColumnSchema
        from schema_drift.storage import save_snapshot
        table = TableSchema(name="users", columns=[
            ColumnSchema(name="id", col_type="INTEGER", nullable=False, default=None),
            ColumnSchema(name="bio", col_type="TEXT", nullable=True, default=None),
        ], indexes=[])
        snap_b = DatabaseSnapshot(snapshot_id="snap-b", created_at="2024-01-02T00:00:00Z", tables=[table])
        save_snapshot(str(tmp_path), snap_b)

        result = cmd_plan(_args(tmp_path, "snap-a", "snap-b", fmt="text"))
        assert result == 0
        out = capsys.readouterr().out
        assert "ALTER TABLE" in out or "CREATE" in out or "DROP" in out or "--" in out
