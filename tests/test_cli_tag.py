"""Tests for schema_drift.cli_tag."""

from __future__ import annotations

import argparse
import pytest

from schema_drift import tagger
from schema_drift.cli_tag import (
    cmd_tag_add,
    cmd_tag_remove,
    cmd_tag_list,
    cmd_tag_find,
)


def _args(storage_dir, **kwargs):
    ns = argparse.Namespace(storage_dir=storage_dir, **kwargs)
    return ns


class TestCmdTagAdd:
    def test_returns_0_on_success(self, tmp_path):
        args = _args(str(tmp_path), snapshot_id="s1", tag="prod")
        assert cmd_tag_add(args) == 0

    def test_tag_persisted(self, tmp_path):
        args = _args(str(tmp_path), snapshot_id="s1", tag="prod")
        cmd_tag_add(args)
        assert "prod" in tagger.get_tags(str(tmp_path), "s1")


class TestCmdTagRemove:
    def test_returns_0_when_tag_exists(self, tmp_path):
        tagger.add_tag(str(tmp_path), "s1", "prod")
        args = _args(str(tmp_path), snapshot_id="s1", tag="prod")
        assert cmd_tag_remove(args) == 0

    def test_returns_1_when_tag_missing(self, tmp_path):
        args = _args(str(tmp_path), snapshot_id="s1", tag="ghost")
        assert cmd_tag_remove(args) == 1


class TestCmdTagList:
    def test_returns_0(self, tmp_path, capsys):
        tagger.add_tag(str(tmp_path), "s1", "alpha")
        args = _args(str(tmp_path), snapshot_id="s1")
        assert cmd_tag_list(args) == 0

    def test_prints_tags(self, tmp_path, capsys):
        tagger.add_tag(str(tmp_path), "s1", "alpha")
        tagger.add_tag(str(tmp_path), "s1", "beta")
        args = _args(str(tmp_path), snapshot_id="s1")
        cmd_tag_list(args)
        out = capsys.readouterr().out
        assert "alpha" in out
        assert "beta" in out

    def test_no_tags_prints_message(self, tmp_path, capsys):
        args = _args(str(tmp_path), snapshot_id="empty")
        cmd_tag_list(args)
        out = capsys.readouterr().out
        assert "No tags" in out


class TestCmdTagFind:
    def test_returns_0(self, tmp_path):
        tagger.add_tag(str(tmp_path), "s1", "prod")
        args = _args(str(tmp_path), tag="prod")
        assert cmd_tag_find(args) == 0

    def test_prints_matching_ids(self, tmp_path, capsys):
        tagger.add_tag(str(tmp_path), "s1", "prod")
        tagger.add_tag(str(tmp_path), "s2", "prod")
        args = _args(str(tmp_path), tag="prod")
        cmd_tag_find(args)
        out = capsys.readouterr().out
        assert "s1" in out
        assert "s2" in out

    def test_no_match_prints_message(self, tmp_path, capsys):
        args = _args(str(tmp_path), tag="missing")
        cmd_tag_find(args)
        out = capsys.readouterr().out
        assert "No snapshots" in out
