"""Tests for schema_drift.cli_audit."""

from __future__ import annotations

import argparse
import json
import pytest

from schema_drift.auditor import record_event
from schema_drift.cli_audit import cmd_audit_log, cmd_audit_clear


def _args(storage_dir: str, use_json: bool = False) -> argparse.Namespace:
    return argparse.Namespace(storage_dir=storage_dir, json=use_json)


class TestCmdAuditLog:
    def test_empty_log_prints_message(self, tmp_path, capsys):
        rc = cmd_audit_log(_args(str(tmp_path)))
        assert rc == 0
        out = capsys.readouterr().out
        assert "No audit log entries" in out

    def test_shows_event_name(self, tmp_path, capsys):
        record_event(str(tmp_path), "snapshot_saved", {"id": "s1"})
        rc = cmd_audit_log(_args(str(tmp_path)))
        assert rc == 0
        out = capsys.readouterr().out
        assert "snapshot_saved" in out

    def test_shows_details(self, tmp_path, capsys):
        record_event(str(tmp_path), "diff_run", {"from": "a", "to": "b"})
        cmd_audit_log(_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "from=a" in out
        assert "to=b" in out

    def test_json_flag_outputs_valid_json(self, tmp_path, capsys):
        record_event(str(tmp_path), "snapshot_saved", {"id": "s1"})
        rc = cmd_audit_log(_args(str(tmp_path), use_json=True))
        assert rc == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert isinstance(parsed, list)
        assert parsed[0]["event"] == "snapshot_saved"

    def test_multiple_entries_all_shown(self, tmp_path, capsys):
        record_event(str(tmp_path), "e1")
        record_event(str(tmp_path), "e2")
        cmd_audit_log(_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "e1" in out
        assert "e2" in out


class TestCmdAuditClear:
    def test_returns_0(self, tmp_path):
        rc = cmd_audit_clear(_args(str(tmp_path)))
        assert rc == 0

    def test_prints_confirmation(self, tmp_path, capsys):
        cmd_audit_clear(_args(str(tmp_path)))
        out = capsys.readouterr().out
        assert "cleared" in out.lower()

    def test_log_empty_after_clear(self, tmp_path):
        record_event(str(tmp_path), "snapshot_saved")
        cmd_audit_clear(_args(str(tmp_path)))
        from schema_drift.auditor import get_audit_log
        assert get_audit_log(str(tmp_path)) == []
