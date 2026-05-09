"""Tests for schema_drift.cli_ignore."""

from __future__ import annotations

import argparse
import os
import pytest

from schema_drift.ignorer import load_ignore_config, save_ignore_config, IgnoreConfig, IgnoreRule
from schema_drift.cli_ignore import cmd_ignore_add, cmd_ignore_list, cmd_ignore_clear


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "ignore_file": "",
        "table": "",
        "column": "",
        "change_type": "",
        "reason": "",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdIgnoreAdd:
    def test_adds_rule_to_new_file(self, tmp_path):
        path = str(tmp_path / "ignore.json")
        args = _args(ignore_file=path, table="users", column="email", change_type="column_added", reason="expected")
        rc = cmd_ignore_add(args)
        assert rc == 0
        cfg = load_ignore_config(path)
        assert len(cfg.rules) == 1
        assert cfg.rules[0].table == "users"

    def test_appends_to_existing_rules(self, tmp_path):
        path = str(tmp_path / "ignore.json")
        existing = IgnoreConfig(rules=[IgnoreRule(table="orders")])
        save_ignore_config(existing, path)
        args = _args(ignore_file=path, table="users")
        cmd_ignore_add(args)
        cfg = load_ignore_config(path)
        assert len(cfg.rules) == 2

    def test_empty_strings_stored_as_none(self, tmp_path):
        path = str(tmp_path / "ignore.json")
        args = _args(ignore_file=path)
        cmd_ignore_add(args)
        cfg = load_ignore_config(path)
        rule = cfg.rules[0]
        assert rule.table is None
        assert rule.column is None
        assert rule.change_type is None


class TestCmdIgnoreList:
    def test_empty_config_prints_message(self, tmp_path, capsys):
        path = str(tmp_path / "ignore.json")
        rc = cmd_ignore_list(_args(ignore_file=path))
        assert rc == 0
        assert "No ignore rules" in capsys.readouterr().out

    def test_lists_rules(self, tmp_path, capsys):
        path = str(tmp_path / "ignore.json")
        cfg = IgnoreConfig(rules=[IgnoreRule(table="users", reason="ok")])
        save_ignore_config(cfg, path)
        cmd_ignore_list(_args(ignore_file=path))
        out = capsys.readouterr().out
        assert "users" in out
        assert "ok" in out


class TestCmdIgnoreClear:
    def test_clears_all_rules(self, tmp_path):
        path = str(tmp_path / "ignore.json")
        cfg = IgnoreConfig(rules=[IgnoreRule(table="users"), IgnoreRule(table="orders")])
        save_ignore_config(cfg, path)
        rc = cmd_ignore_clear(_args(ignore_file=path))
        assert rc == 0
        assert load_ignore_config(path).rules == []
