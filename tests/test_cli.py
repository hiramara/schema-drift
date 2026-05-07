"""Tests for schema_drift.cli — command-line interface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_drift.cli import main
from schema_drift.snapshot import ColumnSchema, DatabaseSnapshot, TableSchema, to_dict
from schema_drift.storage import save_snapshot


def _make_snapshot(snapshot_id: str, col_type: str = "INTEGER") -> DatabaseSnapshot:
    col = ColumnSchema(name="id", data_type=col_type, nullable=False, default=None)
    table = TableSchema(name="users", columns=[col], indexes=[])
    return DatabaseSnapshot(snapshot_id=snapshot_id, tables={"users": table})


class TestListCommand:
    def test_list_empty(self, tmp_path, capsys):
        rc = main(["--dir", str(tmp_path), "list"])
        assert rc == 0
        assert "No snapshots found" in capsys.readouterr().out

    def test_list_shows_ids(self, tmp_path, capsys):
        save_snapshot(_make_snapshot("v1"), directory=str(tmp_path))
        save_snapshot(_make_snapshot("v2"), directory=str(tmp_path))
        main(["--dir", str(tmp_path), "list"])
        out = capsys.readouterr().out
        assert "v1" in out
        assert "v2" in out


class TestSaveCommand:
    def test_save_from_file(self, tmp_path, capsys):
        snap = _make_snapshot("v1")
        json_file = tmp_path / "snap.json"
        json_file.write_text(json.dumps(to_dict(snap)), encoding="utf-8")

        rc = main(["--dir", str(tmp_path / "store"), "save", str(json_file)])
        assert rc == 0
        assert "v1" in capsys.readouterr().out


class TestDiffCommand:
    def test_diff_text_output(self, tmp_path, capsys):
        save_snapshot(_make_snapshot("v1", "INTEGER"), directory=str(tmp_path))
        save_snapshot(_make_snapshot("v2", "BIGINT"), directory=str(tmp_path))

        rc = main(["--dir", str(tmp_path), "diff", "v2", "--before", "v1"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "v1" in out or "v2" in out

    def test_diff_json_output(self, tmp_path, capsys):
        save_snapshot(_make_snapshot("v1"), directory=str(tmp_path))
        save_snapshot(_make_snapshot("v2"), directory=str(tmp_path))

        rc = main(["--dir", str(tmp_path), "diff", "v2", "--before", "v1", "--json"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert "changes" in data

    def test_diff_no_previous_snapshot_returns_error(self, tmp_path, capsys):
        save_snapshot(_make_snapshot("v2"), directory=str(tmp_path))
        rc = main(["--dir", str(tmp_path / "empty"), "diff", "v2"])
        assert rc == 1
