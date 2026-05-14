"""Tests for schema_drift.labeler."""

from __future__ import annotations

import pytest

from schema_drift import labeler


@pytest.fixture()
def storage(tmp_path):
    return str(tmp_path)


class TestSetLabel:
    def test_set_creates_entry(self, storage):
        labeler.set_label(storage, "snap-1", "production baseline")
        assert labeler.get_label(storage, "snap-1") == "production baseline"

    def test_overwrite_updates_label(self, storage):
        labeler.set_label(storage, "snap-1", "old")
        labeler.set_label(storage, "snap-1", "new")
        assert labeler.get_label(storage, "snap-1") == "new"

    def test_multiple_snapshots_independent(self, storage):
        labeler.set_label(storage, "snap-1", "alpha")
        labeler.set_label(storage, "snap-2", "beta")
        assert labeler.get_label(storage, "snap-1") == "alpha"
        assert labeler.get_label(storage, "snap-2") == "beta"


class TestGetLabel:
    def test_returns_none_when_absent(self, storage):
        assert labeler.get_label(storage, "missing") is None

    def test_returns_label_after_set(self, storage):
        labeler.set_label(storage, "snap-x", "release-1")
        assert labeler.get_label(storage, "snap-x") == "release-1"


class TestRemoveLabel:
    def test_returns_true_when_removed(self, storage):
        labeler.set_label(storage, "snap-1", "lbl")
        assert labeler.remove_label(storage, "snap-1") is True

    def test_returns_false_when_absent(self, storage):
        assert labeler.remove_label(storage, "ghost") is False

    def test_label_gone_after_remove(self, storage):
        labeler.set_label(storage, "snap-1", "lbl")
        labeler.remove_label(storage, "snap-1")
        assert labeler.get_label(storage, "snap-1") is None


class TestListLabels:
    def test_empty_returns_empty_dict(self, storage):
        assert labeler.list_labels(storage) == {}

    def test_contains_all_set_labels(self, storage):
        labeler.set_label(storage, "a", "label-a")
        labeler.set_label(storage, "b", "label-b")
        result = labeler.list_labels(storage)
        assert result == {"a": "label-a", "b": "label-b"}


class TestFindByLabel:
    def test_returns_matching_ids(self, storage):
        labeler.set_label(storage, "snap-1", "staging")
        labeler.set_label(storage, "snap-2", "staging")
        labeler.set_label(storage, "snap-3", "prod")
        result = labeler.find_by_label(storage, "staging")
        assert sorted(result) == ["snap-1", "snap-2"]

    def test_returns_empty_when_no_match(self, storage):
        labeler.set_label(storage, "snap-1", "prod")
        assert labeler.find_by_label(storage, "staging") == []

    def test_exact_match_only(self, storage):
        labeler.set_label(storage, "snap-1", "staging-v2")
        assert labeler.find_by_label(storage, "staging") == []
