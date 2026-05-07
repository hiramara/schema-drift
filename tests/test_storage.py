"""Tests for schema_drift.storage — snapshot persistence."""

from __future__ import annotations

import json
import pytest

from schema_drift.snapshot import ColumnSchema, DatabaseSnapshot, TableSchema
from schema_drift.storage import (
    _snapshot_filename,
    latest_snapshot,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


def _make_snapshot(snapshot_id: str) -> DatabaseSnapshot:
    col = ColumnSchema(name="id", data_type="INTEGER", nullable=False, default=None)
    table = TableSchema(name="items", columns=[col], indexes=[])
    return DatabaseSnapshot(snapshot_id=snapshot_id, tables={"items": table})


class TestSnapshotFilename:
    def test_spaces_replaced(self):
        assert _snapshot_filename("my snapshot") == "my_snapshot.json"

    def test_slashes_replaced(self):
        assert _snapshot_filename("prod/v1") == "prod-v1.json"

    def test_plain_id(self):
        assert _snapshot_filename("v1") == "v1.json"


class TestSaveAndLoad:
    def test_round_trip(self, tmp_path):
        snap = _make_snapshot("v1")
        path = save_snapshot(snap, directory=str(tmp_path))
        assert path.exists()

        loaded = load_snapshot("v1", directory=str(tmp_path))
        assert loaded.snapshot_id == "v1"
        assert "items" in loaded.tables

    def test_file_is_valid_json(self, tmp_path):
        snap = _make_snapshot("v2")
        path = save_snapshot(snap, directory=str(tmp_path))
        data = json.loads(path.read_text())
        assert "snapshot_id" in data

    def test_load_missing_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="does_not_exist"):
            load_snapshot("does_not_exist", directory=str(tmp_path))

    def test_directory_created_automatically(self, tmp_path):
        target = tmp_path / "nested" / "dir"
        snap = _make_snapshot("v1")
        save_snapshot(snap, directory=str(target))
        assert target.exists()


class TestListSnapshots:
    def test_empty_directory(self, tmp_path):
        assert list_snapshots(str(tmp_path)) == []

    def test_non_existent_directory(self, tmp_path):
        assert list_snapshots(str(tmp_path / "ghost")) == []

    def test_returns_sorted_ids(self, tmp_path):
        for sid in ["v3", "v1", "v2"]:
            save_snapshot(_make_snapshot(sid), directory=str(tmp_path))
        ids = list_snapshots(str(tmp_path))
        assert ids == sorted(ids)


class TestLatestSnapshot:
    def test_returns_none_when_empty(self, tmp_path):
        assert latest_snapshot(str(tmp_path)) is None

    def test_returns_last_alphabetically(self, tmp_path):
        for sid in ["2024-01-01", "2024-06-01", "2024-03-01"]:
            save_snapshot(_make_snapshot(sid), directory=str(tmp_path))
        snap = latest_snapshot(str(tmp_path))
        assert snap is not None
        assert snap.snapshot_id == "2024-06-01"
