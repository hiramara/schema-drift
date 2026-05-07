"""Tests for schema_drift.scheduler."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import call, patch

import pytest

from schema_drift.scheduler import (
    ScheduleConfig,
    load_schedule_config,
    run_once,
    save_schedule_config,
)


def _default_config(**kwargs) -> ScheduleConfig:
    defaults = dict(
        interval_seconds=600,
        storage_dir="/tmp/snaps",
        snapshot_id_prefix="test",
        notify_on_drift=False,
        max_snapshots=10,
    )
    defaults.update(kwargs)
    return ScheduleConfig(**defaults)


class TestScheduleConfigRoundTrip:
    def test_to_dict_contains_all_keys(self):
        cfg = _default_config()
        d = cfg.to_dict()
        assert "interval_seconds" in d
        assert "storage_dir" in d
        assert "snapshot_id_prefix" in d
        assert "notify_on_drift" in d
        assert "max_snapshots" in d

    def test_from_dict_restores_values(self):
        cfg = _default_config(interval_seconds=120, notify_on_drift=True)
        restored = ScheduleConfig.from_dict(cfg.to_dict())
        assert restored.interval_seconds == 120
        assert restored.notify_on_drift is True

    def test_from_dict_defaults_prefix(self):
        data = {"interval_seconds": 60, "storage_dir": "/tmp"}
        cfg = ScheduleConfig.from_dict(data)
        assert cfg.snapshot_id_prefix == "scheduled"


class TestSaveLoadConfig:
    def test_save_creates_file(self, tmp_path):
        cfg = _default_config(storage_dir=str(tmp_path))
        dest = str(tmp_path / "sched.json")
        save_schedule_config(cfg, dest)
        assert Path(dest).exists()

    def test_load_returns_config(self, tmp_path):
        cfg = _default_config(interval_seconds=300, storage_dir=str(tmp_path))
        dest = str(tmp_path / "sched.json")
        save_schedule_config(cfg, dest)
        loaded = load_schedule_config(dest)
        assert loaded.interval_seconds == 300

    def test_save_writes_valid_json(self, tmp_path):
        cfg = _default_config()
        dest = str(tmp_path / "sched.json")
        save_schedule_config(cfg, dest)
        with open(dest) as fh:
            data = json.load(fh)
        assert data["interval_seconds"] == cfg.interval_seconds


class TestRunOnce:
    def test_calls_snapshot_fn_with_correct_id(self):
        calls = []
        cfg = _default_config(snapshot_id_prefix="ci", storage_dir="/snaps")

        def fake_snap(sid, sdir):
            calls.append((sid, sdir))

        sid = run_once(cfg, fake_snap, timestamp=1_000_000)
        assert sid == "ci-1000000"
        assert calls == [("ci-1000000", "/snaps")]

    def test_returns_snapshot_id(self):
        cfg = _default_config(snapshot_id_prefix="auto")
        sid = run_once(cfg, lambda *a: None, timestamp=42)
        assert sid == "auto-42"
