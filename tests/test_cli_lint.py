"""Tests for schema_drift.cli_lint."""

from __future__ import annotations

import json
import types
from unittest.mock import MagicMock, patch

import pytest

from schema_drift.cli_lint import cmd_lint
from schema_drift.snapshot import ColumnSchema, DatabaseSnapshot, TableSchema
from schema_drift.linter import LintResult, LintIssue


def _make_snapshot(sid="snap-1") -> DatabaseSnapshot:
    col = ColumnSchema(name="id", col_type="INTEGER", nullable=False, default=None)
    table = TableSchema(name="users", columns=[col], indexes=[])
    return DatabaseSnapshot(snapshot_id=sid, tables={"users": table})


def _args(**kwargs):
    base = {"storage_dir": "/tmp", "snapshot_id": "snap-1", "format": "text"}
    base.update(kwargs)
    ns = types.SimpleNamespace(**base)
    return ns


class TestCmdLint:
    def test_missing_snapshot_returns_2(self):
        with patch("schema_drift.cli_lint.load_snapshot", return_value=None):
            rc = cmd_lint(_args())
        assert rc == 2

    def test_clean_snapshot_returns_0(self):
        snap = _make_snapshot()
        with patch("schema_drift.cli_lint.load_snapshot", return_value=snap):
            rc = cmd_lint(_args())
        assert rc == 0

    def test_snapshot_with_errors_returns_1(self, capsys):
        snap = _make_snapshot()
        bad_result = LintResult(
            snapshot_id="snap-1",
            issues=[LintIssue("users", None, "L001", "Table has no columns.", "error")],
        )
        with patch("schema_drift.cli_lint.load_snapshot", return_value=snap), \
             patch("schema_drift.cli_lint.lint_snapshot", return_value=bad_result):
            rc = cmd_lint(_args())
        assert rc == 1

    def test_text_output_contains_code(self, capsys):
        snap = _make_snapshot()
        bad_result = LintResult(
            snapshot_id="snap-1",
            issues=[LintIssue("users", None, "L001", "Table has no columns.", "error")],
        )
        with patch("schema_drift.cli_lint.load_snapshot", return_value=snap), \
             patch("schema_drift.cli_lint.lint_snapshot", return_value=bad_result):
            cmd_lint(_args(format="text"))
        out = capsys.readouterr().out
        assert "L001" in out

    def test_json_format_is_valid_json(self, capsys):
        snap = _make_snapshot()
        with patch("schema_drift.cli_lint.load_snapshot", return_value=snap):
            cmd_lint(_args(format="json"))
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert "snapshot_id" in parsed
        assert "issues" in parsed

    def test_json_format_no_errors_returns_0(self):
        snap = _make_snapshot()
        with patch("schema_drift.cli_lint.load_snapshot", return_value=snap):
            rc = cmd_lint(_args(format="json"))
        assert rc == 0

    def test_warnings_only_returns_0(self, capsys):
        snap = _make_snapshot()
        warn_result = LintResult(
            snapshot_id="snap-1",
            issues=[LintIssue("users", "notes", "L004", "Nullable column.", "warning")],
        )
        with patch("schema_drift.cli_lint.load_snapshot", return_value=snap), \
             patch("schema_drift.cli_lint.lint_snapshot", return_value=warn_result):
            rc = cmd_lint(_args())
        assert rc == 0
