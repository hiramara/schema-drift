"""Tests for schema_drift.exporter."""

from __future__ import annotations

import csv
import io
import json
import datetime

import pytest

from schema_drift.differ import ChangeType, SchemaChange
from schema_drift.exporter import (
    export_diff,
    export_diff_csv,
    export_diff_json,
    export_diff_markdown,
    export_snapshot_json,
)
from schema_drift.snapshot import ColumnSchema, DatabaseSnapshot, TableSchema


def _make_snapshot(sid: str) -> DatabaseSnapshot:
    col = ColumnSchema(name="id", data_type="integer", nullable=False, default=None)
    table = TableSchema(name="users", columns=[col], indexes=[])
    return DatabaseSnapshot(
        snapshot_id=sid,
        captured_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        tables=[table],
    )


def _make_change() -> SchemaChange:
    return SchemaChange(
        change_type=ChangeType.ADDED,
        table="users",
        object_type="column",
        name="email",
        detail="Added column email (varchar)",
    )


class TestExportSnapshotJson:
    def test_returns_valid_json(self):
        snap = _make_snapshot("snap-1")
        raw = export_snapshot_json(snap)
        data = json.loads(raw)
        assert data["snapshot_id"] == "snap-1"

    def test_contains_tables(self):
        snap = _make_snapshot("snap-2")
        data = json.loads(export_snapshot_json(snap))
        assert any(t["name"] == "users" for t in data["tables"])


class TestExportDiffJson:
    def test_includes_snapshot_ids(self):
        old = _make_snapshot("old")
        new = _make_snapshot("new")
        data = json.loads(export_diff_json(old, new, [_make_change()]))
        assert data["old_snapshot_id"] == "old"
        assert data["new_snapshot_id"] == "new"

    def test_changelog_key_present(self):
        old = _make_snapshot("old")
        new = _make_snapshot("new")
        data = json.loads(export_diff_json(old, new, []))
        assert "changelog" in data


class TestExportDiffCsv:
    def test_header_row(self):
        csv_str = export_diff_csv([])
        reader = csv.DictReader(io.StringIO(csv_str))
        assert set(reader.fieldnames) == {"table", "change_type", "object_type", "name", "detail"}

    def test_change_row(self):
        rows = list(csv.DictReader(io.StringIO(export_diff_csv([_make_change()]))))
        assert len(rows) == 1
        assert rows[0]["table"] == "users"
        assert rows[0]["change_type"] == "added"


class TestExportDiffMarkdown:
    def test_returns_string(self):
        old = _make_snapshot("old")
        new = _make_snapshot("new")
        result = export_diff_markdown(old, new, [])
        assert isinstance(result, str)

    def test_contains_snapshot_ids(self):
        old = _make_snapshot("old")
        new = _make_snapshot("new")
        result = export_diff_markdown(old, new, [_make_change()])
        assert "old" in result and "new" in result


class TestExportDiff:
    def test_unknown_format_raises(self):
        old = _make_snapshot("a")
        new = _make_snapshot("b")
        with pytest.raises(ValueError, match="Unknown export format"):
            export_diff(old, new, [], fmt="xml")

    def test_json_format(self):
        old = _make_snapshot("a")
        new = _make_snapshot("b")
        result = export_diff(old, new, [], fmt="json")
        assert json.loads(result)["old_snapshot_id"] == "a"

    def test_csv_format(self):
        old = _make_snapshot("a")
        new = _make_snapshot("b")
        result = export_diff(old, new, [_make_change()], fmt="csv")
        assert "change_type" in result

    def test_markdown_format(self):
        old = _make_snapshot("a")
        new = _make_snapshot("b")
        result = export_diff(old, new, [], fmt="markdown")
        assert isinstance(result, str)
