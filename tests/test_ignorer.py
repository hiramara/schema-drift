"""Tests for schema_drift.ignorer."""

from __future__ import annotations

import json
import os
import pytest

from schema_drift.differ import ChangeType, SchemaChange
from schema_drift.ignorer import (
    IgnoreConfig,
    IgnoreRule,
    apply_ignore,
    load_ignore_config,
    save_ignore_config,
)


def _change(
    table="users",
    column="email",
    change_type=ChangeType.COLUMN_ADDED,
    detail="",
) -> SchemaChange:
    return SchemaChange(table=table, column=column, change_type=change_type, detail=detail)


# ---------------------------------------------------------------------------
# IgnoreRule.matches
# ---------------------------------------------------------------------------

class TestIgnoreRuleMatches:
    def test_matches_exact_table_and_column(self):
        rule = IgnoreRule(table="users", column="email", change_type="column_added")
        assert rule.matches(_change())

    def test_no_match_wrong_table(self):
        rule = IgnoreRule(table="orders", column="email", change_type="column_added")
        assert not rule.matches(_change())

    def test_no_match_wrong_change_type(self):
        rule = IgnoreRule(table="users", column="email", change_type="column_removed")
        assert not rule.matches(_change())

    def test_wildcard_table_matches_any(self):
        rule = IgnoreRule(table=None, column="email", change_type="column_added")
        assert rule.matches(_change(table="orders"))

    def test_wildcard_column_matches_any(self):
        rule = IgnoreRule(table="users", column=None, change_type="column_added")
        assert rule.matches(_change(column="phone"))

    def test_full_wildcard_matches_everything(self):
        rule = IgnoreRule()
        assert rule.matches(_change())


# ---------------------------------------------------------------------------
# IgnoreConfig round-trip
# ---------------------------------------------------------------------------

class TestIgnoreConfigRoundTrip:
    def test_empty_config(self):
        cfg = IgnoreConfig()
        assert IgnoreConfig.from_dict(cfg.to_dict()).rules == []

    def test_rule_preserved(self):
        rule = IgnoreRule(table="t", column="c", change_type="column_added", reason="ok")
        cfg = IgnoreConfig(rules=[rule])
        restored = IgnoreConfig.from_dict(cfg.to_dict())
        r = restored.rules[0]
        assert r.table == "t"
        assert r.column == "c"
        assert r.change_type == "column_added"
        assert r.reason == "ok"


# ---------------------------------------------------------------------------
# apply_ignore
# ---------------------------------------------------------------------------

class TestApplyIgnore:
    def test_no_rules_returns_all(self):
        changes = [_change(), _change(table="orders")]
        assert apply_ignore(changes, IgnoreConfig()) == changes

    def test_matching_rule_removes_change(self):
        cfg = IgnoreConfig(rules=[IgnoreRule(table="users", column="email", change_type="column_added")])
        changes = [_change(), _change(table="orders", column="total", change_type=ChangeType.COLUMN_ADDED)]
        result = apply_ignore(changes, cfg)
        assert len(result) == 1
        assert result[0].table == "orders"

    def test_wildcard_rule_removes_all(self):
        cfg = IgnoreConfig(rules=[IgnoreRule()])
        changes = [_change(), _change(table="orders")]
        assert apply_ignore(changes, cfg) == []


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

class TestIgnoreConfigIO:
    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "ignore.json")
        cfg = IgnoreConfig(rules=[IgnoreRule(table="users", reason="expected")])
        save_ignore_config(cfg, path)
        loaded = load_ignore_config(path)
        assert loaded.rules[0].table == "users"
        assert loaded.rules[0].reason == "expected"

    def test_load_missing_file_returns_empty(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        cfg = load_ignore_config(path)
        assert cfg.rules == []
