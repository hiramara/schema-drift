"""Tests for schema_drift.summarizer."""

from __future__ import annotations

import pytest

from schema_drift.differ import SchemaChange, ChangeType
from schema_drift.snapshot import DatabaseSnapshot, TableSchema, ColumnSchema
from schema_drift.comparator import ComparisonResult
from schema_drift.summarizer import summarize, DriftSummary


def _col(name: str, col_type: str = "TEXT") -> ColumnSchema:
    return ColumnSchema(name=name, col_type=col_type, nullable=True, default=None)


def _snap(snap_id: str) -> DatabaseSnapshot:
    table = TableSchema(name="users", columns=[_col("id", "INT")], indexes=[])
    return DatabaseSnapshot(snapshot_id=snap_id, tables={"users": table})


def _change(change_type: ChangeType, table: str = "users", column: str = "email") -> SchemaChange:
    return SchemaChange(
        table=table,
        change_type=change_type,
        column=column,
        before=None,
        after=None,
    )


def _result(changes: list) -> ComparisonResult:
    return ComparisonResult(
        from_snapshot=_snap("snap-1"),
        to_snapshot=_snap("snap-2"),
        changes=changes,
    )


class TestSummarize:
    def test_empty_changes(self):
        summary = summarize(_result([]))
        assert summary.total_changes == 0
        assert summary.critical_count == 0
        assert summary.warning_count == 0
        assert summary.info_count == 0

    def test_snapshot_ids_captured(self):
        summary = summarize(_result([]))
        assert summary.from_id == "snap-1"
        assert summary.to_id == "snap-2"

    def test_column_removed_is_critical(self):
        summary = summarize(_result([_change(ChangeType.COLUMN_REMOVED)]))
        assert summary.critical_count == 1
        assert summary.warning_count == 0
        assert summary.info_count == 0

    def test_column_modified_is_warning(self):
        summary = summarize(_result([_change(ChangeType.COLUMN_MODIFIED)]))
        assert summary.warning_count == 1
        assert summary.critical_count == 0

    def test_column_added_is_info(self):
        summary = summarize(_result([_change(ChangeType.COLUMN_ADDED)]))
        assert summary.info_count == 1

    def test_by_type_counts(self):
        changes = [
            _change(ChangeType.COLUMN_ADDED),
            _change(ChangeType.COLUMN_ADDED),
            _change(ChangeType.COLUMN_REMOVED),
        ]
        summary = summarize(_result(changes))
        assert summary.by_type[ChangeType.COLUMN_ADDED.value] == 2
        assert summary.by_type[ChangeType.COLUMN_REMOVED.value] == 1

    def test_by_table_counts(self):
        changes = [
            _change(ChangeType.COLUMN_ADDED, table="orders"),
            _change(ChangeType.COLUMN_REMOVED, table="users"),
            _change(ChangeType.COLUMN_ADDED, table="orders"),
        ]
        summary = summarize(_result(changes))
        assert summary.by_table["orders"] == 2
        assert summary.by_table["users"] == 1

    def test_to_dict_has_all_keys(self):
        summary = summarize(_result([_change(ChangeType.COLUMN_ADDED)]))
        d = summary.to_dict()
        for key in ("from_id", "to_id", "total_changes", "by_type",
                    "by_table", "critical_count", "warning_count", "info_count"):
            assert key in d

    def test_total_changes_matches_list_length(self):
        changes = [_change(ChangeType.COLUMN_ADDED) for _ in range(5)]
        summary = summarize(_result(changes))
        assert summary.total_changes == 5
