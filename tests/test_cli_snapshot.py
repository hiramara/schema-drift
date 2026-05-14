"""Tests for schema_drift.cli_snapshot — capture sub-command."""

from __future__ import annotations

import argparse
import types
from unittest.mock import MagicMock, patch

import pytest

from schema_drift.cli_snapshot import cmd_capture, register_snapshot_commands
from schema_drift.snapshot import ColumnSchema, DatabaseSnapshot, TableSchema


def _make_snapshot(sid: str = "snap-1") -> DatabaseSnapshot:
    return DatabaseSnapshot(
        snapshot_id=sid,
        captured_at="2024-01-01T00:00:00+00:00",
        tables=[
            TableSchema(
                name="users",
                columns=[ColumnSchema(name="id", data_type="INTEGER", nullable=False)],
                indexes=[],
            )
        ],
    )


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "dsn": "sqlite:///:memory:",
        "id": "snap-1",
        "tables": None,
        "storage_dir": ".schema_drift",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdCapture:
    def test_returns_0_on_success(self, tmp_path):
        snap = _make_snapshot()
        with (
            patch("schema_drift.cli_snapshot.capture_snapshot", return_value=snap),
            patch("schema_drift.cli_snapshot.save_snapshot") as mock_save,
        ):
            code = cmd_capture(_args(storage_dir=str(tmp_path)))
        assert code == 0
        mock_save.assert_called_once()

    def test_snapshot_id_passed_through(self, tmp_path):
        snap = _make_snapshot("v2")
        with (
            patch("schema_drift.cli_snapshot.capture_snapshot", return_value=snap) as mock_cap,
            patch("schema_drift.cli_snapshot.save_snapshot"),
        ):
            cmd_capture(_args(id="v2", storage_dir=str(tmp_path)))
        _, kwargs = mock_cap.call_args
        assert mock_cap.call_args[1]["snapshot_id"] == "v2" or mock_cap.call_args[0][1] == "v2"

    def test_tables_flag_parsed_correctly(self, tmp_path):
        snap = _make_snapshot()
        with (
            patch("schema_drift.cli_snapshot.capture_snapshot", return_value=snap) as mock_cap,
            patch("schema_drift.cli_snapshot.save_snapshot"),
        ):
            cmd_capture(_args(tables="users,posts", storage_dir=str(tmp_path)))
        call_tables = mock_cap.call_args[1].get("tables") or mock_cap.call_args[0][2]
        assert set(call_tables) == {"users", "posts"}

    def test_none_tables_when_flag_absent(self, tmp_path):
        snap = _make_snapshot()
        with (
            patch("schema_drift.cli_snapshot.capture_snapshot", return_value=snap) as mock_cap,
            patch("schema_drift.cli_snapshot.save_snapshot"),
        ):
            cmd_capture(_args(tables=None, storage_dir=str(tmp_path)))
        call_tables = mock_cap.call_args[1].get("tables") or mock_cap.call_args[0][2]
        assert call_tables is None

    def test_returns_1_on_capture_error(self, tmp_path, capsys):
        with patch(
            "schema_drift.cli_snapshot.capture_snapshot",
            side_effect=RuntimeError("connection refused"),
        ):
            code = cmd_capture(_args(storage_dir=str(tmp_path)))
        assert code == 1
        captured = capsys.readouterr()
        assert "connection refused" in captured.err


class TestRegisterSnapshotCommands:
    def test_capture_subcommand_registered(self):
        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        register_snapshot_commands(subs)
        ns = parser.parse_args(["capture", "sqlite:///:memory:", "snap-1"])
        assert ns.dsn == "sqlite:///:memory:"
        assert ns.id == "snap-1"
