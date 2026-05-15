"""Tests for schema_drift.scorer."""

from __future__ import annotations

import pytest

from schema_drift.comparator import ComparisonResult
from schema_drift.differ import ChangeType, SchemaChange
from schema_drift.scorer import DriftScore, _risk_level, score_diff


def _change(change_type: ChangeType, table: str = "users", column: str | None = None) -> SchemaChange:
    return SchemaChange(
        change_type=change_type,
        table=table,
        column=column,
        detail="",
    )


def _result(*changes: SchemaChange) -> ComparisonResult:
    return ComparisonResult(
        from_snapshot_id="snap-a",
        to_snapshot_id="snap-b",
        changes=list(changes),
    )


class TestRiskLevel:
    def test_zero_is_none(self):
        assert _risk_level(0) == "none"

    def test_low_boundary(self):
        assert _risk_level(1) == "low"
        assert _risk_level(9) == "low"

    def test_medium_boundary(self):
        assert _risk_level(10) == "medium"
        assert _risk_level(24) == "medium"

    def test_high_boundary(self):
        assert _risk_level(25) == "high"
        assert _risk_level(49) == "high"

    def test_critical_boundary(self):
        assert _risk_level(50) == "critical"
        assert _risk_level(999) == "critical"


class TestScoreDiff:
    def test_no_changes_returns_zero(self):
        score = score_diff(_result())
        assert score.total == 0
        assert score.risk_level == "none"
        assert score.breakdown == {}

    def test_single_column_removed_scores_ten(self):
        score = score_diff(_result(_change(ChangeType.COLUMN_REMOVED)))
        assert score.total == 10
        assert score.risk_level == "medium"

    def test_single_column_added_scores_three(self):
        score = score_diff(_result(_change(ChangeType.COLUMN_ADDED)))
        assert score.total == 3
        assert score.risk_level == "low"

    def test_multiple_changes_accumulate(self):
        score = score_diff(
            _result(
                _change(ChangeType.COLUMN_REMOVED),
                _change(ChangeType.INDEX_REMOVED),
                _change(ChangeType.COLUMN_TYPE_CHANGED),
            )
        )
        assert score.total == 10 + 8 + 7  # 25
        assert score.risk_level == "high"

    def test_breakdown_groups_by_change_type(self):
        score = score_diff(
            _result(
                _change(ChangeType.COLUMN_ADDED, column="a"),
                _change(ChangeType.COLUMN_ADDED, column="b"),
                _change(ChangeType.COLUMN_REMOVED, column="c"),
            )
        )
        assert score.breakdown[ChangeType.COLUMN_ADDED.value] == 6
        assert score.breakdown[ChangeType.COLUMN_REMOVED.value] == 10

    def test_to_dict_contains_required_keys(self):
        score = score_diff(_result(_change(ChangeType.COLUMN_ADDED)))
        d = score.to_dict()
        assert "total" in d
        assert "risk_level" in d
        assert "breakdown" in d

    def test_index_removed_contributes_to_critical(self):
        changes = [_change(ChangeType.INDEX_REMOVED) for _ in range(7)]
        score = score_diff(_result(*changes))
        assert score.total == 56
        assert score.risk_level == "critical"
