"""Tests for schema_drift.cli_schedule."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from schema_drift.cli_schedule import (
    cmd_schedule_init,
    cmd_schedule_show,
    register_schedule_commands,
)


def _args(**kwargs):
    defaults = dict(
        config="schedule.json",
        interval=3600,
        storage_dir="snapshots",
        prefix="scheduled",
        notify=False,
        max_snapshots=50,
    )
    defaults.update(kwargs)
    ns = argparse.Namespace(**defaults)
    return ns


class TestCmdScheduleInit:
    def test_creates_config_file(self, tmp_path):
        dest = str(tmp_path / "sched.json")
        rc = cmd_schedule_init(_args(config=dest, storage_dir=str(tmp_path)))
        assert rc == 0
        assert Path(dest).exists()

    def test_written_json_has_interval(self, tmp_path):
        dest = str(tmp_path / "sched.json")
        cmd_schedule_init(_args(config=dest, interval=120, storage_dir=str(tmp_path)))
        data = json.loads(Path(dest).read_text())
        assert data["interval_seconds"] == 120

    def test_notify_flag_stored(self, tmp_path):
        dest = str(tmp_path / "sched.json")
        cmd_schedule_init(_args(config=dest, notify=True, storage_dir=str(tmp_path)))
        data = json.loads(Path(dest).read_text())
        assert data["notify_on_drift"] is True


class TestCmdScheduleShow:
    def test_missing_config_returns_2(self, tmp_path):
        rc = cmd_schedule_show(_args(config=str(tmp_path / "nope.json")))
        assert rc == 2

    def test_shows_interval(self, tmp_path, capsys):
        dest = str(tmp_path / "sched.json")
        cmd_schedule_init(_args(config=dest, interval=900, storage_dir=str(tmp_path)))
        rc = cmd_schedule_show(_args(config=dest))
        assert rc == 0
        out = capsys.readouterr().out
        assert "900" in out


class TestRegisterScheduleCommands:
    def test_registers_schedule_init(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_schedule_commands(sub)
        args = parser.parse_args(["schedule-init", "--interval", "60"])
        assert args.interval == 60

    def test_registers_schedule_show(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_schedule_commands(sub)
        args = parser.parse_args(["schedule-show", "--config", "my.json"])
        assert args.config == "my.json"
