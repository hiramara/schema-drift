"""Tests for schema_drift.aliaser."""

from __future__ import annotations

import pytest

from schema_drift.aliaser import (
    find_aliases_for,
    list_aliases,
    remove_alias,
    resolve_alias,
    set_alias,
)


@pytest.fixture()
def storage(tmp_path):
    return str(tmp_path)


class TestSetAlias:
    def test_resolve_returns_id_after_set(self, storage):
        set_alias(storage, "prod-baseline", "snap-001")
        assert resolve_alias(storage, "prod-baseline") == "snap-001"

    def test_overwrite_updates_id(self, storage):
        set_alias(storage, "prod-baseline", "snap-001")
        set_alias(storage, "prod-baseline", "snap-002")
        assert resolve_alias(storage, "prod-baseline") == "snap-002"

    def test_multiple_aliases_independent(self, storage):
        set_alias(storage, "alpha", "snap-001")
        set_alias(storage, "beta", "snap-002")
        assert resolve_alias(storage, "alpha") == "snap-001"
        assert resolve_alias(storage, "beta") == "snap-002"


class TestRemoveAlias:
    def test_returns_true_when_removed(self, storage):
        set_alias(storage, "old", "snap-001")
        assert remove_alias(storage, "old") is True

    def test_returns_false_when_not_found(self, storage):
        assert remove_alias(storage, "ghost") is False

    def test_resolve_returns_none_after_removal(self, storage):
        set_alias(storage, "temp", "snap-003")
        remove_alias(storage, "temp")
        assert resolve_alias(storage, "temp") is None


class TestResolveAlias:
    def test_returns_none_for_unknown_alias(self, storage):
        assert resolve_alias(storage, "nonexistent") is None

    def test_returns_correct_id(self, storage):
        set_alias(storage, "v1", "snap-abc")
        assert resolve_alias(storage, "v1") == "snap-abc"


class TestListAliases:
    def test_empty_when_no_aliases(self, storage):
        assert list_aliases(storage) == []

    def test_returns_all_aliases_sorted(self, storage):
        set_alias(storage, "zebra", "snap-z")
        set_alias(storage, "alpha", "snap-a")
        result = list_aliases(storage)
        assert [r["alias"] for r in result] == ["alpha", "zebra"]

    def test_each_entry_has_required_keys(self, storage):
        set_alias(storage, "myalias", "snap-x")
        entry = list_aliases(storage)[0]
        assert "alias" in entry
        assert "snapshot_id" in entry


class TestFindAliasesFor:
    def test_returns_empty_when_no_match(self, storage):
        assert find_aliases_for(storage, "snap-999") == []

    def test_returns_single_alias(self, storage):
        set_alias(storage, "release", "snap-007")
        assert find_aliases_for(storage, "snap-007") == ["release"]

    def test_returns_multiple_aliases_for_same_id(self, storage):
        set_alias(storage, "latest", "snap-007")
        set_alias(storage, "stable", "snap-007")
        aliases = sorted(find_aliases_for(storage, "snap-007"))
        assert aliases == ["latest", "stable"]
