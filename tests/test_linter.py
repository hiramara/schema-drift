"""Tests for schema_drift.linter."""

from __future__ import annotations

import pytest

from schema_drift.snapshot import ColumnSchema, DatabaseSnapshot, TableSchema
from schema_drift.linter import LintIssue, LintResult, lint_snapshot


def _col(name: str, col_type: str = "TEXT", nullable: bool = False, default=None) -> ColumnSchema:
    return ColumnSchema(name=name, col_type=col_type, nullable=nullable, default=default)


def _snap(*tables: TableSchema, sid: str = "snap-1") -> DatabaseSnapshot:
    return DatabaseSnapshot(
        snapshot_id=sid,
        tables={t.name: t for t in tables},
    )


def _table(name: str, columns: list) -> TableSchema:
    return TableSchema(name=name, columns=columns, indexes=[])


class TestLintResult:
    def test_no_issues_has_issues_false(self):
        r = LintResult(snapshot_id="s1")
        assert not r.has_issues

    def test_with_issue_has_issues_true(self):
        r = LintResult(snapshot_id="s1", issues=[LintIssue("t", None, "L001", "msg", "error")])
        assert r.has_issues

    def test_error_count(self):
        r = LintResult(snapshot_id="s1", issues=[
            LintIssue("t", None, "L001", "msg", "error"),
            LintIssue("t", "c", "L004", "msg", "warning"),
        ])
        assert r.error_count == 1
        assert r.warning_count == 1

    def test_to_dict_keys(self):
        r = LintResult(snapshot_id="s1")
        d = r.to_dict()
        assert set(d.keys()) == {"snapshot_id", "error_count", "warning_count", "issues"}


class TestLintSnapshot:
    def test_clean_snapshot_has_no_issues(self):
        snap = _snap(_table("users", [_col("id", "INTEGER"), _col("name", "TEXT")]))
        result = lint_snapshot(snap)
        assert not result.has_issues

    def test_empty_table_raises_l001(self):
        snap = _snap(_table("empty_table", []))
        result = lint_snapshot(snap)
        codes = [i.code for i in result.issues]
        assert "L001" in codes

    def test_column_without_type_raises_l002(self):
        snap = _snap(_table("t", [_col("id", ""), _col("name", "TEXT")]))
        result = lint_snapshot(snap)
        codes = [i.code for i in result.issues]
        assert "L002" in codes

    def test_l002_issue_references_correct_column(self):
        snap = _snap(_table("t", [_col("bad_col", "  ")]))
        result = lint_snapshot(snap)
        l002 = [i for i in result.issues if i.code == "L002"]
        assert len(l002) == 1
        assert l002[0].column == "bad_col"

    def test_duplicate_column_name_raises_l003(self):
        snap = _snap(_table("t", [_col("Id", "INTEGER"), _col("id", "TEXT")]))
        result = lint_snapshot(snap)
        codes = [i.code for i in result.issues]
        assert "L003" in codes

    def test_nullable_no_default_raises_l004(self):
        snap = _snap(_table("t", [_col("notes", "TEXT", nullable=True, default=None)]))
        result = lint_snapshot(snap)
        codes = [i.code for i in result.issues]
        assert "L004" in codes

    def test_nullable_with_default_no_l004(self):
        snap = _snap(_table("t", [_col("notes", "TEXT", nullable=True, default="")])) 
        result = lint_snapshot(snap)
        codes = [i.code for i in result.issues]
        assert "L004" not in codes

    def test_snapshot_id_preserved(self):
        snap = _snap(_table("t", [_col("id", "INTEGER")]), sid="my-snap")
        result = lint_snapshot(snap)
        assert result.snapshot_id == "my-snap"

    def test_multiple_tables_all_checked(self):
        snap = _snap(
            _table("a", []),
            _table("b", []),
        )
        result = lint_snapshot(snap)
        tables_with_l001 = {i.table for i in result.issues if i.code == "L001"}
        assert tables_with_l001 == {"a", "b"}
