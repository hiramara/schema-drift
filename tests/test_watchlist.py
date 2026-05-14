"""Tests for schema_drift.watchlist."""

from __future__ import annotations

import pytest

from schema_drift import watchlist


@pytest.fixture()
def storage(tmp_path):
    return str(tmp_path)


class TestAddWatch:
    def test_returns_true_when_newly_added(self, storage):
        assert watchlist.add_watch(storage, "users") is True

    def test_returns_false_when_duplicate(self, storage):
        watchlist.add_watch(storage, "users")
        assert watchlist.add_watch(storage, "users") is False

    def test_table_and_column_stored(self, storage):
        watchlist.add_watch(storage, "orders", column="total")
        entries = watchlist.list_watches(storage)
        assert any(e["table"] == "orders" and e["column"] == "total" for e in entries)

    def test_reason_stored(self, storage):
        watchlist.add_watch(storage, "payments", reason="PCI sensitive")
        entries = watchlist.list_watches(storage)
        assert entries[0]["reason"] == "PCI sensitive"

    def test_table_and_column_treated_independently(self, storage):
        watchlist.add_watch(storage, "users")
        watchlist.add_watch(storage, "users", column="email")
        assert len(watchlist.list_watches(storage)) == 2


class TestRemoveWatch:
    def test_returns_true_when_removed(self, storage):
        watchlist.add_watch(storage, "users")
        assert watchlist.remove_watch(storage, "users") is True

    def test_returns_false_when_not_present(self, storage):
        assert watchlist.remove_watch(storage, "ghost") is False

    def test_entry_gone_after_remove(self, storage):
        watchlist.add_watch(storage, "users")
        watchlist.remove_watch(storage, "users")
        assert watchlist.list_watches(storage) == []

    def test_only_matching_entry_removed(self, storage):
        watchlist.add_watch(storage, "users")
        watchlist.add_watch(storage, "orders")
        watchlist.remove_watch(storage, "users")
        entries = watchlist.list_watches(storage)
        assert len(entries) == 1
        assert entries[0]["table"] == "orders"


class TestIsWatched:
    def test_true_for_watched_table(self, storage):
        watchlist.add_watch(storage, "users")
        assert watchlist.is_watched(storage, "users") is True

    def test_false_for_unwatched_table(self, storage):
        assert watchlist.is_watched(storage, "users") is False

    def test_column_level_watch(self, storage):
        watchlist.add_watch(storage, "users", column="ssn")
        assert watchlist.is_watched(storage, "users", column="ssn") is True
        assert watchlist.is_watched(storage, "users") is False


class TestClearWatchlist:
    def test_returns_count_cleared(self, storage):
        watchlist.add_watch(storage, "a")
        watchlist.add_watch(storage, "b")
        assert watchlist.clear_watchlist(storage) == 2

    def test_empty_after_clear(self, storage):
        watchlist.add_watch(storage, "a")
        watchlist.clear_watchlist(storage)
        assert watchlist.list_watches(storage) == []

    def test_clear_on_empty_returns_zero(self, storage):
        assert watchlist.clear_watchlist(storage) == 0
