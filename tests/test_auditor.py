"""Tests for schema_drift.auditor."""

from __future__ import annotations

import json
import pytest

from schema_drift.auditor import (
    AuditEntry,
    record_event,
    get_audit_log,
    clear_audit_log,
    _audit_path,
)


@pytest.fixture()
def storage(tmp_path):
    return str(tmp_path)


class TestAuditEntryRoundTrip:
    def test_to_dict_has_required_keys(self):
        entry = AuditEntry(event="snapshot_saved", timestamp="2024-01-01T00:00:00+00:00")
        d = entry.to_dict()
        assert d["event"] == "snapshot_saved"
        assert d["timestamp"] == "2024-01-01T00:00:00+00:00"
        assert d["details"] == {}

    def test_from_dict_restores_fields(self):
        data = {"event": "diff_run", "timestamp": "2024-06-01T12:00:00+00:00", "details": {"from": "a", "to": "b"}}
        entry = AuditEntry.from_dict(data)
        assert entry.event == "diff_run"
        assert entry.details == {"from": "a", "to": "b"}

    def test_from_dict_defaults_details(self):
        data = {"event": "baseline_set", "timestamp": "2024-01-01T00:00:00+00:00"}
        entry = AuditEntry.from_dict(data)
        assert entry.details == {}


class TestRecordEvent:
    def test_creates_file_on_first_record(self, storage):
        record_event(storage, "snapshot_saved")
        assert _audit_path(storage).exists()

    def test_single_entry_written(self, storage):
        record_event(storage, "snapshot_saved", {"id": "snap-1"})
        entries = get_audit_log(storage)
        assert len(entries) == 1
        assert entries[0].event == "snapshot_saved"
        assert entries[0].details["id"] == "snap-1"

    def test_multiple_entries_appended(self, storage):
        record_event(storage, "snapshot_saved", {"id": "snap-1"})
        record_event(storage, "diff_run", {"from": "snap-1", "to": "snap-2"})
        entries = get_audit_log(storage)
        assert len(entries) == 2
        assert entries[1].event == "diff_run"

    def test_returns_entry(self, storage):
        entry = record_event(storage, "baseline_set", {"id": "snap-1"})
        assert isinstance(entry, AuditEntry)
        assert entry.event == "baseline_set"

    def test_timestamp_is_set(self, storage):
        entry = record_event(storage, "snapshot_saved")
        assert entry.timestamp != ""
        assert "T" in entry.timestamp


class TestGetAuditLog:
    def test_empty_when_no_file(self, storage):
        entries = get_audit_log(storage)
        assert entries == []

    def test_returns_all_entries(self, storage):
        record_event(storage, "e1")
        record_event(storage, "e2")
        record_event(storage, "e3")
        assert len(get_audit_log(storage)) == 3


class TestClearAuditLog:
    def test_removes_file(self, storage):
        record_event(storage, "snapshot_saved")
        clear_audit_log(storage)
        assert not _audit_path(storage).exists()

    def test_clear_on_empty_is_noop(self, storage):
        clear_audit_log(storage)  # should not raise
        assert get_audit_log(storage) == []

    def test_log_empty_after_clear(self, storage):
        record_event(storage, "snapshot_saved")
        clear_audit_log(storage)
        assert get_audit_log(storage) == []
