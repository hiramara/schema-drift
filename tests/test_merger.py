"""Tests for schema_drift.merger."""
import pytest

from schema_drift.snapshot import (
    DatabaseSnapshot,
    TableSchema,
    ColumnSchema,
)
from schema_drift.merger import merge_snapshots, MergeResult


def _col(name: str, col_type: str = "TEXT") -> ColumnSchema:
    return ColumnSchema(name=name, col_type=col_type, nullable=True, default=None)


def _table(name: str, *col_names: str) -> TableSchema:
    cols = {c: _col(c) for c in col_names}
    return TableSchema(name=name, columns=cols, indexes={})


def _snap(snap_id: str, *table_names: str) -> DatabaseSnapshot:
    tables = {t: _table(t, "id", "value") for t in table_names}
    return DatabaseSnapshot(snapshot_id=snap_id, created_at="2024-01-01T00:00:00", tables=tables)


class TestMergeSnapshots:
    def test_returns_merge_result(self):
        base = _snap("base", "users")
        override = _snap("override", "orders")
        result = merge_snapshots(base, override)
        assert isinstance(result, MergeResult)

    def test_merged_snapshot_contains_all_tables(self):
        base = _snap("base", "users", "products")
        override = _snap("override", "orders")
        result = merge_snapshots(base, override)
        assert set(result.snapshot.tables.keys()) == {"users", "products", "orders"}

    def test_override_strategy_replaces_existing_table(self):
        base = _snap("base", "users")
        override = _snap("override", "users")
        # Give the override table a distinct column
        override.tables["users"] = _table("users", "id", "email", "phone")
        result = merge_snapshots(base, override, strategy="override")
        assert "phone" in result.snapshot.tables["users"].columns

    def test_additive_strategy_keeps_base_table(self):
        base = _snap("base", "users")
        base.tables["users"] = _table("users", "id", "name")
        override = _snap("override", "users")
        override.tables["users"] = _table("users", "id", "email")
        result = merge_snapshots(base, override, strategy="additive")
        # Base version should be retained
        assert "name" in result.snapshot.tables["users"].columns
        assert "email" not in result.snapshot.tables["users"].columns

    def test_added_tables_tracked(self):
        base = _snap("base", "users")
        override = _snap("override", "orders", "payments")
        result = merge_snapshots(base, override)
        assert set(result.added_tables) == {"orders", "payments"}

    def test_overwritten_tables_tracked(self):
        base = _snap("base", "users", "products")
        override = _snap("override", "users")
        result = merge_snapshots(base, override, strategy="override")
        assert "users" in result.overwritten_tables
        assert "products" not in result.overwritten_tables

    def test_custom_merged_id(self):
        base = _snap("base", "users")
        override = _snap("override", "orders")
        result = merge_snapshots(base, override, merged_id="combined-v1")
        assert result.snapshot.snapshot_id == "combined-v1"

    def test_default_merged_id_combines_both_ids(self):
        base = _snap("snap-a", "users")
        override = _snap("snap-b", "orders")
        result = merge_snapshots(base, override)
        assert result.snapshot.snapshot_id == "snap-a+snap-b"

    def test_invalid_strategy_raises(self):
        base = _snap("base", "users")
        override = _snap("override", "orders")
        with pytest.raises(ValueError, match="Unknown merge strategy"):
            merge_snapshots(base, override, strategy="unknown")

    def test_to_dict_contains_expected_keys(self):
        base = _snap("base", "users")
        override = _snap("override", "orders")
        result = merge_snapshots(base, override)
        d = result.to_dict()
        assert "snapshot" in d
        assert "added_tables" in d
        assert "overwritten_tables" in d
        assert "kept_tables" in d
        assert d["total_tables"] == 2
