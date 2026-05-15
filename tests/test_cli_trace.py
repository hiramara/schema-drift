"""Tests for schema_drift.cli_trace."""

from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest

from schema_drift.cli_trace import cmd_trace
from schema_drift.snapshot import ColumnSchema, DatabaseSnapshot, TableSchema


def _col(name: str, col_type: str = "TEXT") -> ColumnSchema:
    return ColumnSchema(name=name, col_type=col_type, nullable=True)


def _make_snapshot(sid: str) -> DatabaseSnapshot:
    tbl = TableSchema(
        name="orders",
        columns={"id": _col("id", "INT"), "amount": _col("amount", "FLOAT")},
        indexes={},
    )
    return DatabaseSnapshot(snapshot_id=sid, tables={"orders": tbl})


def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        snapshot_ids=["s1", "s2"],
        table="orders",
        column=None,
        json=False,
        storage_dir="/fake",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdTrace:
    def test_missing_snapshot_returns_2(self):
        with patch("schema_drift.cli_trace.load_snapshot", return_value=None):
            rc = cmd_trace(_args())
        assert rc == 2

    def test_returns_0_on_success(self, capsys):
        snaps = [_make_snapshot("s1"), _make_snapshot("s2")]
        with patch("schema_drift.cli_trace.load_snapshot", side_effect=snaps):
            rc = cmd_trace(_args())
        assert rc == 0

    def test_table_trace_printed(self, capsys):
        snaps = [_make_snapshot("s1"), _make_snapshot("s2")]
        with patch("schema_drift.cli_trace.load_snapshot", side_effect=snaps):
            cmd_trace(_args())
        out = capsys.readouterr().out
        assert "orders" in out
        assert "True" in out

    def test_json_output_parseable(self, capsys):
        snaps = [_make_snapshot("s1")]
        with patch("schema_drift.cli_trace.load_snapshot", side_effect=snaps):
            rc = cmd_trace(_args(snapshot_ids=["s1"], json=True))
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["table"] == "orders"
        assert isinstance(data["entries"], list)

    def test_column_trace_in_json(self, capsys):
        snaps = [_make_snapshot("s1")]
        with patch("schema_drift.cli_trace.load_snapshot", side_effect=snaps):
            rc = cmd_trace(_args(snapshot_ids=["s1"], column="amount", json=True))
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["column"] == "amount"
        assert data["entries"][0]["exists"] is True

    def test_no_snapshots_returns_2(self):
        rc = cmd_trace(_args(snapshot_ids=[]))
        assert rc == 2
