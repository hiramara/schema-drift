"""Tests for schema_drift.baseline."""

from __future__ import annotations

import json
import os
import pytest

from schema_drift.baseline import (
    BASELINE_FILENAME,
    set_baseline,
    get_baseline,
    clear_baseline,
    baseline_info,
)


@pytest.fixture()
def storage(tmp_path):
    return str(tmp_path)


class TestGetBaseline:
    def test_returns_none_when_no_file(self, storage):
        assert get_baseline(storage) is None

    def test_returns_id_after_set(self, storage):
        set_baseline(storage, "snap-001")
        assert get_baseline(storage) == "snap-001"

    def test_overwrite_updates_id(self, storage):
        set_baseline(storage, "snap-001")
        set_baseline(storage, "snap-002")
        assert get_baseline(storage) == "snap-002"


class TestSetBaseline:
    def test_creates_file(self, storage):
        set_baseline(storage, "snap-abc")
        path = os.path.join(storage, BASELINE_FILENAME)
        assert os.path.exists(path)

    def test_file_contains_valid_json(self, storage):
        set_baseline(storage, "snap-xyz")
        path = os.path.join(storage, BASELINE_FILENAME)
        with open(path) as fh:
            data = json.load(fh)
        assert data["baseline_id"] == "snap-xyz"

    def test_creates_missing_parent_dirs(self, tmp_path):
        nested = str(tmp_path / "a" / "b" / "c")
        set_baseline(nested, "snap-nested")
        assert get_baseline(nested) == "snap-nested"


class TestClearBaseline:
    def test_returns_false_when_nothing_to_clear(self, storage):
        assert clear_baseline(storage) is False

    def test_returns_true_when_file_removed(self, storage):
        set_baseline(storage, "snap-001")
        assert clear_baseline(storage) is True

    def test_get_returns_none_after_clear(self, storage):
        set_baseline(storage, "snap-001")
        clear_baseline(storage)
        assert get_baseline(storage) is None


class TestBaselineInfo:
    def test_is_set_false_when_no_baseline(self, storage):
        info = baseline_info(storage)
        assert info["is_set"] is False
        assert info["baseline_id"] is None

    def test_is_set_true_after_set(self, storage):
        set_baseline(storage, "snap-007")
        info = baseline_info(storage)
        assert info["is_set"] is True
        assert info["baseline_id"] == "snap-007"

    def test_contains_storage_dir(self, storage):
        info = baseline_info(storage)
        assert info["storage_dir"] == storage
