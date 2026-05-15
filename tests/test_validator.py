"""Tests for schema_drift.validator."""
import pytest

from schema_drift.snapshot import (
    ColumnSchema,
    DatabaseSnapshot,
    IndexSchema,
    TableSchema,
)
from schema_drift.validator import validate_snapshot, ValidationResult


def _col(name: str, *, nullable: bool = False, primary_key: bool = False) -> ColumnSchema:
    return ColumnSchema(
        name=name,
        data_type="INTEGER",
        nullable=nullable,
        primary_key=primary_key,
        default=None,
        unique=False,
    )


def _idx(name: str) -> IndexSchema:
    return IndexSchema(name=name, columns=["id"], unique=False)


def _snap(*tables: TableSchema, snapshot_id: str = "snap-1") -> DatabaseSnapshot:
    return DatabaseSnapshot(
        snapshot_id=snapshot_id,
        captured_at="2024-01-01T00:00:00Z",
        tables={t.name: t for t in tables},
    )


def _table(name: str, columns, indexes=None) -> TableSchema:
    return TableSchema(name=name, columns=columns, indexes=indexes or [])


class TestValidateSnapshot:
    def test_returns_validation_result(self):
        snap = _snap(_table("users", [_col("id", primary_key=True)]))
        result = validate_snapshot(snap)
        assert isinstance(result, ValidationResult)

    def test_snapshot_id_preserved(self):
        snap = _snap(_table("users", [_col("id", primary_key=True)]), snapshot_id="abc-123")
        result = validate_snapshot(snap)
        assert result.snapshot_id == "abc-123"

    def test_clean_snapshot_has_no_issues(self):
        snap = _snap(_table("users", [_col("id", primary_key=True)], [_idx("pk_users")]))
        result = validate_snapshot(snap)
        assert not result.has_issues
        assert result.issue_count == 0

    def test_nullable_primary_key_raises_issue(self):
        snap = _snap(_table("orders", [_col("id", nullable=True, primary_key=True)]))
        result = validate_snapshot(snap)
        assert result.has_issues
        rules = [i.rule for i in result.issues]
        assert "no_nullable_primary_keys" in rules

    def test_nullable_pk_issue_references_correct_column(self):
        snap = _snap(_table("orders", [_col("order_id", nullable=True, primary_key=True)]))
        result = validate_snapshot(snap)
        issue = next(i for i in result.issues if i.rule == "no_nullable_primary_keys")
        assert issue.column == "order_id"
        assert issue.table == "orders"

    def test_table_without_primary_key_raises_issue(self):
        snap = _snap(_table("logs", [_col("message")]))
        result = validate_snapshot(snap)
        rules = [i.rule for i in result.issues]
        assert "no_tables_without_primary_key" in rules

    def test_unnamed_index_raises_issue(self):
        snap = _snap(_table(
            "users",
            [_col("id", primary_key=True)],
            [IndexSchema(name="", columns=["id"], unique=False)],
        ))
        result = validate_snapshot(snap)
        rules = [i.rule for i in result.issues]
        assert "no_unnamed_indexes" in rules

    def test_to_dict_contains_required_keys(self):
        snap = _snap(_table("users", [_col("id", primary_key=True)]))
        d = validate_snapshot(snap).to_dict()
        assert "snapshot_id" in d
        assert "has_issues" in d
        assert "issue_count" in d
        assert "issues" in d

    def test_multiple_tables_multiple_issues(self):
        snap = _snap(
            _table("a", [_col("x")]),
            _table("b", [_col("y")]),
        )
        result = validate_snapshot(snap)
        tables_with_issues = {i.table for i in result.issues}
        assert "a" in tables_with_issues
        assert "b" in tables_with_issues
