"""Tests for schema_drift.notifier."""
import pytest

from schema_drift.comparator import ComparisonResult
from schema_drift.differ import ChangeType, SchemaChange
from schema_drift.notifier import (
    NotificationConfig,
    build_notification,
    _change_severity,
)


def _change(change_type: ChangeType, table: str = "users", obj: str = "email") -> SchemaChange:
    return SchemaChange(
        table_name=table,
        change_type=change_type,
        object_name=obj,
        detail={},
    )


def _result(*changes: SchemaChange) -> ComparisonResult:
    return ComparisonResult(
        from_snapshot_id="snap-1",
        to_snapshot_id="snap-2",
        changes=list(changes),
    )


class TestChangeSeverity:
    def test_column_removed_is_critical(self):
        assert _change_severity(ChangeType.COLUMN_REMOVED) == "critical"

    def test_index_removed_is_critical(self):
        assert _change_severity(ChangeType.INDEX_REMOVED) == "critical"

    def test_column_modified_is_warning(self):
        assert _change_severity(ChangeType.COLUMN_MODIFIED) == "warning"

    def test_column_added_is_info(self):
        assert _change_severity(ChangeType.COLUMN_ADDED) == "info"


class TestBuildNotification:
    def test_no_changes_returns_none(self):
        result = _result()
        assert build_notification(result) is None

    def test_single_added_column_returns_notification(self):
        result = _result(_change(ChangeType.COLUMN_ADDED))
        notif = build_notification(result)
        assert notif is not None
        assert notif.total_changes == 1
        assert notif.info == 1
        assert notif.critical == 0

    def test_snapshot_ids_preserved(self):
        result = _result(_change(ChangeType.COLUMN_REMOVED))
        notif = build_notification(result)
        assert notif.from_snapshot_id == "snap-1"
        assert notif.to_snapshot_id == "snap-2"

    def test_severity_filter_excludes_info(self):
        result = _result(
            _change(ChangeType.COLUMN_ADDED),
            _change(ChangeType.COLUMN_REMOVED),
        )
        cfg = NotificationConfig(min_severity="warning")
        notif = build_notification(result, cfg)
        assert notif is not None
        assert notif.total_changes == 1
        assert notif.critical == 1
        assert notif.info == 0

    def test_critical_filter_only_critical(self):
        result = _result(
            _change(ChangeType.COLUMN_ADDED),
            _change(ChangeType.COLUMN_MODIFIED),
            _change(ChangeType.COLUMN_REMOVED),
        )
        cfg = NotificationConfig(min_severity="critical")
        notif = build_notification(result, cfg)
        assert notif.total_changes == 1

    def test_include_tables_filter(self):
        result = _result(
            _change(ChangeType.COLUMN_REMOVED, table="users"),
            _change(ChangeType.COLUMN_REMOVED, table="orders"),
        )
        cfg = NotificationConfig(include_tables=["users"])
        notif = build_notification(result, cfg)
        assert notif.total_changes == 1

    def test_exclude_tables_filter(self):
        result = _result(
            _change(ChangeType.COLUMN_REMOVED, table="users"),
            _change(ChangeType.COLUMN_REMOVED, table="orders"),
        )
        cfg = NotificationConfig(exclude_tables=["orders"])
        notif = build_notification(result, cfg)
        assert notif.total_changes == 1

    def test_as_text_contains_snapshot_ids(self):
        result = _result(_change(ChangeType.COLUMN_REMOVED))
        notif = build_notification(result)
        text = notif.as_text()
        assert "snap-1" in text
        assert "snap-2" in text

    def test_as_text_contains_severity_label(self):
        result = _result(_change(ChangeType.COLUMN_REMOVED))
        notif = build_notification(result)
        assert "[CRITICAL]" in notif.as_text()

    def test_all_info_below_warning_threshold_returns_none(self):
        result = _result(_change(ChangeType.COLUMN_ADDED))
        cfg = NotificationConfig(min_severity="warning")
        assert build_notification(result, cfg) is None
