"""Tests for schema_drift.archiver."""

import pytest

from schema_drift.archiver import (
    archive_snapshot,
    unarchive_snapshot,
    list_archived,
    is_archived,
    clear_archive,
)


@pytest.fixture()
def storage(tmp_path):
    return str(tmp_path)


class TestArchiveSnapshot:
    def test_returns_true_when_newly_added(self, storage):
        assert archive_snapshot(storage, "snap-001") is True

    def test_returns_false_when_already_archived(self, storage):
        archive_snapshot(storage, "snap-001")
        assert archive_snapshot(storage, "snap-001") is False

    def test_id_appears_in_list(self, storage):
        archive_snapshot(storage, "snap-002")
        assert "snap-002" in list_archived(storage)

    def test_multiple_ids_stored(self, storage):
        archive_snapshot(storage, "a")
        archive_snapshot(storage, "b")
        assert list_archived(storage) == ["a", "b"]


class TestUnarchiveSnapshot:
    def test_returns_true_when_removed(self, storage):
        archive_snapshot(storage, "snap-001")
        assert unarchive_snapshot(storage, "snap-001") is True

    def test_returns_false_when_not_present(self, storage):
        assert unarchive_snapshot(storage, "snap-999") is False

    def test_id_gone_after_unarchive(self, storage):
        archive_snapshot(storage, "snap-001")
        unarchive_snapshot(storage, "snap-001")
        assert "snap-001" not in list_archived(storage)

    def test_other_ids_unaffected(self, storage):
        archive_snapshot(storage, "a")
        archive_snapshot(storage, "b")
        unarchive_snapshot(storage, "a")
        assert list_archived(storage) == ["b"]


class TestIsArchived:
    def test_true_for_archived(self, storage):
        archive_snapshot(storage, "snap-x")
        assert is_archived(storage, "snap-x") is True

    def test_false_for_unknown(self, storage):
        assert is_archived(storage, "snap-x") is False

    def test_false_after_unarchive(self, storage):
        archive_snapshot(storage, "snap-x")
        unarchive_snapshot(storage, "snap-x")
        assert is_archived(storage, "snap-x") is False


class TestListArchived:
    def test_empty_when_no_file(self, storage):
        assert list_archived(storage) == []

    def test_order_preserved(self, storage):
        for sid in ["c", "a", "b"]:
            archive_snapshot(storage, sid)
        assert list_archived(storage) == ["c", "a", "b"]


class TestClearArchive:
    def test_returns_count(self, storage):
        archive_snapshot(storage, "x")
        archive_snapshot(storage, "y")
        assert clear_archive(storage) == 2

    def test_list_empty_after_clear(self, storage):
        archive_snapshot(storage, "x")
        clear_archive(storage)
        assert list_archived(storage) == []

    def test_clear_on_empty_returns_zero(self, storage):
        assert clear_archive(storage) == 0
