"""Tests for schema_drift.reporter."""

from __future__ import annotations

import pytest

from schema_drift.differ import SchemaChange, ChangeType
from schema_drift.snapshot import DatabaseSnapshot, TableSchema, ColumnSchema
from schema_drift.reporter import generate_markdown_report, generate_html_report


def _make_snapshot(snapshot_id: str) -> DatabaseSnapshot:
    col = ColumnSchema(name="id", data_type="integer", nullable=False, default=None)
    table = TableSchema(name="users", columns=[col], indexes=[])
    return DatabaseSnapshot(snapshot_id=snapshot_id, tables={"users": table})


def _make_change(
    change_type: ChangeType,
    table: str = "users",
    object_name: str = "email",
    detail: str = "varchar(255)",
) -> SchemaChange:
    return SchemaChange(
        change_type=change_type,
        table=table,
        object_name=object_name,
        detail=detail,
    )


class TestMarkdownReport:
    def test_no_changes_message(self):
        old = _make_snapshot("snap-1")
        new = _make_snapshot("snap-2")
        md = generate_markdown_report([], old, new)
        assert "No schema changes detected" in md

    def test_header_contains_snapshot_ids(self):
        old = _make_snapshot("snap-A")
        new = _make_snapshot("snap-B")
        md = generate_markdown_report([], old, new)
        assert "snap-A" in md
        assert "snap-B" in md

    def test_added_change_row_present(self):
        old = _make_snapshot("s1")
        new = _make_snapshot("s2")
        change = _make_change(ChangeType.ADDED)
        md = generate_markdown_report([change], old, new)
        assert "added" in md.lower()
        assert "email" in md
        assert "users" in md

    def test_removed_change_row_present(self):
        old = _make_snapshot("s1")
        new = _make_snapshot("s2")
        change = _make_change(ChangeType.REMOVED, object_name="phone")
        md = generate_markdown_report([change], old, new)
        assert "removed" in md.lower()
        assert "phone" in md

    def test_summary_count(self):
        old = _make_snapshot("s1")
        new = _make_snapshot("s2")
        changes = [
            _make_change(ChangeType.ADDED),
            _make_change(ChangeType.MODIFIED, object_name="name"),
        ]
        md = generate_markdown_report(changes, old, new)
        assert "2 change" in md

    def test_table_header_present(self):
        old = _make_snapshot("s1")
        new = _make_snapshot("s2")
        change = _make_change(ChangeType.ADDED)
        md = generate_markdown_report([change], old, new)
        assert "| # |" in md


class TestHtmlReport:
    def test_returns_html_doctype(self):
        old = _make_snapshot("s1")
        new = _make_snapshot("s2")
        html = generate_html_report([], old, new)
        assert html.strip().startswith("<!DOCTYPE html>")

    def test_no_changes_shows_empty_message(self):
        old = _make_snapshot("s1")
        new = _make_snapshot("s2")
        html = generate_html_report([], old, new)
        assert "No schema changes detected" in html

    def test_added_row_has_css_class(self):
        old = _make_snapshot("s1")
        new = _make_snapshot("s2")
        change = _make_change(ChangeType.ADDED)
        html = generate_html_report([change], old, new)
        assert 'class="added"' in html

    def test_removed_row_has_css_class(self):
        old = _make_snapshot("s1")
        new = _make_snapshot("s2")
        change = _make_change(ChangeType.REMOVED)
        html = generate_html_report([change], old, new)
        assert 'class="removed"' in html

    def test_snapshot_ids_in_html(self):
        old = _make_snapshot("snap-X")
        new = _make_snapshot("snap-Y")
        html = generate_html_report([], old, new)
        assert "snap-X" in html
        assert "snap-Y" in html
