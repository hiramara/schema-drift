"""Tests for schema_drift.cli_stats."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from schema_drift.cli_stats import cmd_stats, register_stats_commands
from schema_drift.snapshot import DatabaseSnapshot, TableSchema, ColumnSchema
from schema_drift.differ import SchemaChange, ChangeType


def _make_snapshot(snap_id: str = "snap1") -> DatabaseSnapshot:
    col = ColumnSchema(name="id", col_type="INTEGER", nullable=False, default=None)
    table = TableSchema(name="users", columns=[col], indexes=[])
    return DatabaseSnapshot(snapshot_id=snap_id, captured_at="2024-01-01T00:00:00", tables=[table])


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "from_id": "snap1",
        "to_id": "snap2",
        "storage_dir": ".schema_drift",
        "json": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdStats:
    def test_missing_from_snapshot_returns_2(self, tmp_path):
        args = _args(storage_dir=str(tmp_path))
        with patch("schema_drift.cli_stats.load_snapshot", return_value=None):
            result = cmd_stats(args)
        assert result == 2

    def test_missing_to_snapshot_returns_2(self, tmp_path):
        snap = _make_snapshot("snap1")
        args = _args(storage_dir=str(tmp_path))
        with patch("schema_drift.cli_stats.load_snapshot", side_effect=[snap, None]):
            result = cmd_stats(args)
        assert result == 2

    def test_returns_0_on_success(self, tmp_path, capsys):
        snap1 = _make_snapshot("snap1")
        snap2 = _make_snapshot("snap2")
        args = _args(storage_dir=str(tmp_path))
        with patch("schema_drift.cli_stats.load_snapshot", side_effect=[snap1, snap2]):
            result = cmd_stats(args)
        assert result == 0

    def test_json_flag_produces_valid_json(self, tmp_path, capsys):
        snap1 = _make_snapshot("snap1")
        snap2 = _make_snapshot("snap2")
        args = _args(storage_dir=str(tmp_path), json=True)
        with patch("schema_drift.cli_stats.load_snapshot", side_effect=[snap1, snap2]):
            cmd_stats(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "total" in data
        assert "tables_affected" in data

    def test_text_output_contains_total(self, tmp_path, capsys):
        snap1 = _make_snapshot("snap1")
        snap2 = _make_snapshot("snap2")
        args = _args(storage_dir=str(tmp_path), json=False)
        with patch("schema_drift.cli_stats.load_snapshot", side_effect=[snap1, snap2]):
            cmd_stats(args)
        captured = capsys.readouterr()
        assert "Total changes" in captured.out


def test_register_stats_commands_adds_subparser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register_stats_commands(subparsers)
    args = parser.parse_args(["stats", "snap1", "snap2"])
    assert args.from_id == "snap1"
    assert args.to_id == "snap2"
