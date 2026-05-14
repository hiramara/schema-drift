"""Tests for schema_drift.pinner."""

import pytest

from schema_drift.pinner import (
    get_label,
    is_pinned,
    list_pins,
    pin_snapshot,
    unpin_snapshot,
)


@pytest.fixture()
def storage(tmp_path):
    return str(tmp_path)


# ---------------------------------------------------------------------------
# pin_snapshot
# ---------------------------------------------------------------------------

class TestPinSnapshot:
    def test_returns_true_when_newly_pinned(self, storage):
        assert pin_snapshot(storage, "snap-1") is True

    def test_returns_false_when_already_pinned(self, storage):
        pin_snapshot(storage, "snap-1")
        assert pin_snapshot(storage, "snap-1") is False

    def test_label_stored(self, storage):
        pin_snapshot(storage, "snap-1", label="release-v2")
        assert get_label(storage, "snap-1") == "release-v2"

    def test_label_updated_on_repin(self, storage):
        pin_snapshot(storage, "snap-1", label="old")
        pin_snapshot(storage, "snap-1", label="new")
        assert get_label(storage, "snap-1") == "new"

    def test_empty_label_default(self, storage):
        pin_snapshot(storage, "snap-1")
        assert get_label(storage, "snap-1") == ""


# ---------------------------------------------------------------------------
# unpin_snapshot
# ---------------------------------------------------------------------------

class TestUnpinSnapshot:
    def test_returns_true_when_removed(self, storage):
        pin_snapshot(storage, "snap-1")
        assert unpin_snapshot(storage, "snap-1") is True

    def test_returns_false_when_not_pinned(self, storage):
        assert unpin_snapshot(storage, "snap-missing") is False

    def test_is_pinned_false_after_unpin(self, storage):
        pin_snapshot(storage, "snap-1")
        unpin_snapshot(storage, "snap-1")
        assert is_pinned(storage, "snap-1") is False


# ---------------------------------------------------------------------------
# is_pinned
# ---------------------------------------------------------------------------

class TestIsPinned:
    def test_false_before_pin(self, storage):
        assert is_pinned(storage, "snap-x") is False

    def test_true_after_pin(self, storage):
        pin_snapshot(storage, "snap-x")
        assert is_pinned(storage, "snap-x") is True


# ---------------------------------------------------------------------------
# list_pins
# ---------------------------------------------------------------------------

class TestListPins:
    def test_empty_when_no_pins(self, storage):
        assert list_pins(storage) == []

    def test_lists_all_pins(self, storage):
        pin_snapshot(storage, "snap-b", label="beta")
        pin_snapshot(storage, "snap-a", label="alpha")
        pins = list_pins(storage)
        assert len(pins) == 2

    def test_sorted_by_id(self, storage):
        pin_snapshot(storage, "snap-b")
        pin_snapshot(storage, "snap-a")
        ids = [p["id"] for p in list_pins(storage)]
        assert ids == sorted(ids)

    def test_dict_has_id_and_label_keys(self, storage):
        pin_snapshot(storage, "snap-1", label="lbl")
        entry = list_pins(storage)[0]
        assert entry["id"] == "snap-1"
        assert entry["label"] == "lbl"
