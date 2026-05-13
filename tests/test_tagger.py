"""Tests for schema_drift.tagger."""

from __future__ import annotations

import json
import os
import pytest

from schema_drift import tagger


@pytest.fixture()
def storage(tmp_path):
    return str(tmp_path)


class TestAddTag:
    def test_adds_single_tag(self, storage):
        tagger.add_tag(storage, "snap1", "production")
        assert "production" in tagger.get_tags(storage, "snap1")

    def test_duplicate_tag_not_doubled(self, storage):
        tagger.add_tag(storage, "snap1", "production")
        tagger.add_tag(storage, "snap1", "production")
        assert tagger.get_tags(storage, "snap1").count("production") == 1

    def test_multiple_tags_stored(self, storage):
        tagger.add_tag(storage, "snap1", "alpha")
        tagger.add_tag(storage, "snap1", "beta")
        tags = tagger.get_tags(storage, "snap1")
        assert "alpha" in tags
        assert "beta" in tags


class TestRemoveTag:
    def test_remove_existing_tag(self, storage):
        tagger.add_tag(storage, "snap1", "release")
        removed = tagger.remove_tag(storage, "snap1", "release")
        assert removed is True
        assert "release" not in tagger.get_tags(storage, "snap1")

    def test_remove_absent_tag_returns_false(self, storage):
        removed = tagger.remove_tag(storage, "snap1", "nonexistent")
        assert removed is False


class TestGetTags:
    def test_returns_empty_list_for_unknown_snapshot(self, storage):
        assert tagger.get_tags(storage, "unknown") == []

    def test_persists_across_calls(self, storage):
        tagger.add_tag(storage, "snap2", "stable")
        # Re-load from disk
        result = tagger.get_tags(storage, "snap2")
        assert result == ["stable"]


class TestFindByTag:
    def test_finds_correct_snapshots(self, storage):
        tagger.add_tag(storage, "snap1", "prod")
        tagger.add_tag(storage, "snap2", "prod")
        tagger.add_tag(storage, "snap3", "staging")
        found = tagger.find_by_tag(storage, "prod")
        assert set(found) == {"snap1", "snap2"}

    def test_returns_empty_when_no_match(self, storage):
        assert tagger.find_by_tag(storage, "missing") == []


class TestClearTags:
    def test_clears_all_tags(self, storage):
        tagger.add_tag(storage, "snap1", "a")
        tagger.add_tag(storage, "snap1", "b")
        tagger.clear_tags(storage, "snap1")
        assert tagger.get_tags(storage, "snap1") == []

    def test_clear_unknown_snapshot_is_noop(self, storage):
        # Should not raise
        tagger.clear_tags(storage, "ghost")


class TestAllTags:
    def test_returns_full_mapping(self, storage):
        tagger.add_tag(storage, "snap1", "x")
        tagger.add_tag(storage, "snap2", "y")
        mapping = tagger.all_tags(storage)
        assert mapping["snap1"] == ["x"]
        assert mapping["snap2"] == ["y"]

    def test_empty_storage_returns_empty_dict(self, storage):
        assert tagger.all_tags(storage) == {}
