"""Tests for schema_drift.retainer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_drift.retainer import (
    apply_retention,
    load_policy,
    save_policy,
)
from schema_drift.storage import save_snapshot
from schema_drift.snapshot import DatabaseSnapshot, TableSchema, ColumnSchema


def _make_snapshot(snap_id: str) -> DatabaseSnapshot:
    col = ColumnSchema(name="id", data_type="INTEGER", nullable=False, default=None)
    table = TableSchema(name="t", columns=[col], indexes=[])
    return DatabaseSnapshot(id=snap_id, captured_at="2024-01-01T00:00:00Z", tables=[table])


@pytest.fixture()
def storage(tmp_path):
    return str(tmp_path)


# ---------------------------------------------------------------------------
# Policy round-trip
# ---------------------------------------------------------------------------

class TestPolicyRoundTrip:
    def test_save_and_load(self, storage):
        save_policy(storage, max_snapshots=5)
        policy = load_policy(storage)
        assert policy["max_snapshots"] == 5
        assert policy["keep_pinned"] is True

    def test_defaults_when_no_file(self, storage):
        policy = load_policy(storage)
        assert policy["max_snapshots"] is None
        assert policy["keep_pinned"] is True

    def test_keep_pinned_false_stored(self, storage):
        save_policy(storage, max_snapshots=3, keep_pinned=False)
        policy = load_policy(storage)
        assert policy["keep_pinned"] is False


# ---------------------------------------------------------------------------
# apply_retention
# ---------------------------------------------------------------------------

class TestApplyRetention:
    def _populate(self, storage, count):
        """Save *count* snapshots named snap-0 … snap-(count-1)."""
        for i in range(count):
            save_snapshot(storage, _make_snapshot(f"snap-{i}"))

    def test_no_policy_removes_nothing(self, storage):
        self._populate(storage, 5)
        removed = apply_retention(storage)
        assert removed == []

    def test_removes_oldest_when_over_limit(self, storage):
        self._populate(storage, 5)
        save_policy(storage, max_snapshots=3)
        removed = apply_retention(storage)
        assert len(removed) == 2

    def test_files_actually_deleted(self, storage):
        self._populate(storage, 4)
        save_policy(storage, max_snapshots=2)
        removed = apply_retention(storage)
        for snap_id in removed:
            files = list(Path(storage).glob(f"*{snap_id}*"))
            assert files == [], f"File for {snap_id} should be deleted"

    def test_within_limit_removes_nothing(self, storage):
        self._populate(storage, 3)
        save_policy(storage, max_snapshots=5)
        removed = apply_retention(storage)
        assert removed == []

    def test_pinned_snapshot_preserved(self, storage):
        self._populate(storage, 4)
        save_policy(storage, max_snapshots=3, keep_pinned=True)
        # Pin the oldest snapshot
        removed = apply_retention(storage, pinned_ids=["snap-0"])
        assert "snap-0" not in removed

    def test_pinned_ignored_when_keep_pinned_false(self, storage):
        self._populate(storage, 4)
        save_policy(storage, max_snapshots=3, keep_pinned=False)
        removed = apply_retention(storage, pinned_ids=["snap-0"])
        # snap-0 is oldest, should be removed despite being in pinned list
        assert "snap-0" in removed
