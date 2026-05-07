"""Tests for schema_drift.cli_notify."""
import argparse
from unittest.mock import patch

import pytest

from schema_drift.cli_notify import cmd_notify, register_notify_commands
from schema_drift.differ import ChangeType, SchemaChange
from schema_drift.comparator import ComparisonResult
from schema_drift.snapshot import DatabaseSnapshot, TableSchema, ColumnSchema


def _make_snapshot(snap_id: str) -> DatabaseSnapshot:
    col = ColumnSchema(name="id", data_type="integer", nullable=False, default=None)
    table = TableSchema(name="users", columns=[col], indexes=[])
    return DatabaseSnapshot(snapshot_id=snap_id, tables={"users": table})


def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        from_id="snap-1",
        to_id="snap-2",
        storage_dir=".schema_drift",
        min_severity="info",
        include_tables=None,
        exclude_tables=None,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdNotify:
    def test_missing_from_snapshot_returns_2(self, tmp_path):
        args = _args(storage_dir=str(tmp_path))
        code = cmd_notify(args)
        assert code == 2

    def test_missing_to_snapshot_returns_2(self, tmp_path):
        from schema_drift.storage import save_snapshot
        snap = _make_snapshot("snap-1")
        save_snapshot(str(tmp_path), snap)
        args = _args(storage_dir=str(tmp_path), from_id="snap-1", to_id="snap-99")
        code = cmd_notify(args)
        assert code == 2

    def test_no_drift_returns_0(self, tmp_path, capsys):
        from schema_drift.storage import save_snapshot
        snap = _make_snapshot("snap-1")
        save_snapshot(str(tmp_path), snap)
        snap2 = _make_snapshot("snap-2")
        save_snapshot(str(tmp_path), snap2)
        args = _args(storage_dir=str(tmp_path))
        code = cmd_notify(args)
        assert code == 0
        out = capsys.readouterr().out
        assert "No significant" in out

    def test_drift_returns_1(self, tmp_path, capsys):
        from schema_drift.storage import save_snapshot
        from schema_drift.snapshot import DatabaseSnapshot, TableSchema, ColumnSchema

        col1 = ColumnSchema(name="id", data_type="integer", nullable=False, default=None)
        t1 = TableSchema(name="users", columns=[col1], indexes=[])
        snap1 = DatabaseSnapshot(snapshot_id="snap-1", tables={"users": t1})
        save_snapshot(str(tmp_path), snap1)

        col2 = ColumnSchema(name="id", data_type="integer", nullable=False, default=None)
        col3 = ColumnSchema(name="email", data_type="text", nullable=True, default=None)
        t2 = TableSchema(name="users", columns=[col2, col3], indexes=[])
        snap2 = DatabaseSnapshot(snapshot_id="snap-2", tables={"users": t2})
        save_snapshot(str(tmp_path), snap2)

        args = _args(storage_dir=str(tmp_path))
        code = cmd_notify(args)
        assert code == 1
        out = capsys.readouterr().out
        assert "snap-1" in out
        assert "snap-2" in out

    def test_severity_filter_suppresses_info(self, tmp_path, capsys):
        from schema_drift.storage import save_snapshot
        from schema_drift.snapshot import DatabaseSnapshot, TableSchema, ColumnSchema

        col1 = ColumnSchema(name="id", data_type="integer", nullable=False, default=None)
        t1 = TableSchema(name="users", columns=[col1], indexes=[])
        snap1 = DatabaseSnapshot(snapshot_id="snap-1", tables={"users": t1})
        save_snapshot(str(tmp_path), snap1)

        col2 = ColumnSchema(name="id", data_type="integer", nullable=False, default=None)
        col3 = ColumnSchema(name="email", data_type="text", nullable=True, default=None)
        t2 = TableSchema(name="users", columns=[col2, col3], indexes=[])
        snap2 = DatabaseSnapshot(snapshot_id="snap-2", tables={"users": t2})
        save_snapshot(str(tmp_path), snap2)

        args = _args(storage_dir=str(tmp_path), min_severity="warning")
        code = cmd_notify(args)
        assert code == 0


class TestRegisterNotifyCommands:
    def test_notify_subcommand_registered(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        register_notify_commands(subparsers)
        ns = parser.parse_args(["notify", "snap-1", "snap-2"])
        assert ns.from_id == "snap-1"
        assert ns.to_id == "snap-2"
        assert ns.min_severity == "info"
