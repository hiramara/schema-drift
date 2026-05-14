"""Tests for schema_drift.cli_label."""

from __future__ import annotations

import argparse
import pytest

from schema_drift import labeler
from schema_drift.cli_label import (
    cmd_label_set,
    cmd_label_remove,
    cmd_label_get,
    cmd_label_list,
    cmd_label_find,
)


def _args(storage_dir, **kwargs):
    ns = argparse.Namespace(storage_dir=storage_dir, **kwargs)
    return ns


@pytest.fixture()
def storage(tmp_path):
    return str(tmp_path)


class TestCmdLabelSet:
    def test_returns_0(self, storage):
        assert cmd_label_set(_args(storage, snapshot_id="s1", label="lbl")) == 0

    def test_label_persisted(self, storage):
        cmd_label_set(_args(storage, snapshot_id="s1", label="my-label"))
        assert labeler.get_label(storage, "s1") == "my-label"


class TestCmdLabelRemove:
    def test_returns_0_when_exists(self, storage):
        labeler.set_label(storage, "s1", "lbl")
        assert cmd_label_remove(_args(storage, snapshot_id="s1")) == 0

    def test_returns_1_when_absent(self, storage):
        assert cmd_label_remove(_args(storage, snapshot_id="ghost")) == 1


class TestCmdLabelGet:
    def test_returns_0_when_found(self, storage, capsys):
        labeler.set_label(storage, "s1", "hello")
        rc = cmd_label_get(_args(storage, snapshot_id="s1"))
        assert rc == 0
        assert "hello" in capsys.readouterr().out

    def test_returns_1_when_missing(self, storage):
        assert cmd_label_get(_args(storage, snapshot_id="none")) == 1


class TestCmdLabelList:
    def test_no_labels_message(self, storage, capsys):
        cmd_label_list(_args(storage))
        assert "No labels" in capsys.readouterr().out

    def test_shows_all_labels(self, storage, capsys):
        labeler.set_label(storage, "s1", "alpha")
        labeler.set_label(storage, "s2", "beta")
        cmd_label_list(_args(storage))
        out = capsys.readouterr().out
        assert "alpha" in out
        assert "beta" in out


class TestCmdLabelFind:
    def test_returns_matching_ids(self, storage, capsys):
        labeler.set_label(storage, "s1", "prod")
        labeler.set_label(storage, "s2", "staging")
        cmd_label_find(_args(storage, label="prod"))
        assert "s1" in capsys.readouterr().out

    def test_no_match_message(self, storage, capsys):
        rc = cmd_label_find(_args(storage, label="missing"))
        assert rc == 0
        assert "No snapshots" in capsys.readouterr().out
