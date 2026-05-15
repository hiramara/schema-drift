"""Tests for schema_drift.planner."""

from __future__ import annotations

import pytest

from schema_drift.differ import SchemaChange, ChangeType
from schema_drift.planner import MigrationStep, MigrationPlan, plan_migration


def _change(
    change_type: ChangeType,
    table: str = "users",
    column: str | None = None,
    old_value=None,
    new_value=None,
) -> SchemaChange:
    return SchemaChange(
        change_type=change_type,
        table=table,
        column=column,
        description=f"{change_type.value} on {table}",
        old_value=old_value,
        new_value=new_value,
    )


class TestPlanMigration:
    def test_empty_changes_returns_empty_plan(self):
        plan = plan_migration([])
        assert plan.step_count == 0
        assert plan.steps == []

    def test_single_column_added(self):
        c = _change(ChangeType.COLUMN_ADDED, column="email", new_value={"type": "VARCHAR"})
        plan = plan_migration([c])
        assert plan.step_count == 1
        step = plan.steps[0]
        assert step.order == 1
        assert step.change_type == ChangeType.COLUMN_ADDED.value
        assert "ADD COLUMN email VARCHAR" in step.sql_hint

    def test_column_removed_comes_before_column_added(self):
        add = _change(ChangeType.COLUMN_ADDED, column="bio")
        remove = _change(ChangeType.COLUMN_REMOVED, column="old_col")
        plan = plan_migration([add, remove])
        assert plan.steps[0].change_type == ChangeType.COLUMN_REMOVED.value
        assert plan.steps[1].change_type == ChangeType.COLUMN_ADDED.value

    def test_table_removed_ordered_after_column_removed(self):
        tbl = _change(ChangeType.TABLE_REMOVED)
        col = _change(ChangeType.COLUMN_REMOVED, column="x")
        plan = plan_migration([tbl, col])
        types = [s.change_type for s in plan.steps]
        assert types.index(ChangeType.COLUMN_REMOVED.value) < types.index(ChangeType.TABLE_REMOVED.value)

    def test_step_orders_are_sequential(self):
        changes = [
            _change(ChangeType.COLUMN_ADDED, column="a"),
            _change(ChangeType.INDEX_ADDED, column="idx_a"),
            _change(ChangeType.COLUMN_REMOVED, column="b"),
        ]
        plan = plan_migration(changes)
        orders = [s.order for s in plan.steps]
        assert orders == list(range(1, len(changes) + 1))

    def test_to_dict_contains_step_count(self):
        plan = plan_migration([_change(ChangeType.TABLE_ADDED, table="orders")])
        d = plan.to_dict()
        assert d["step_count"] == 1
        assert len(d["steps"]) == 1

    def test_migration_step_to_dict_keys(self):
        step = MigrationStep(
            order=1,
            change_type="column_added",
            table="t",
            description="desc",
            sql_hint="ALTER TABLE t ADD COLUMN x TEXT;",
        )
        d = step.to_dict()
        for key in ("order", "change_type", "table", "description", "sql_hint"):
            assert key in d

    def test_column_modified_hint_is_comment(self):
        c = _change(ChangeType.COLUMN_MODIFIED, column="age", new_value={"type": "BIGINT"})
        plan = plan_migration([c])
        assert plan.steps[0].sql_hint.startswith("--")

    def test_table_added_hint_contains_create(self):
        c = _change(ChangeType.TABLE_ADDED, table="payments")
        plan = plan_migration([c])
        assert "CREATE TABLE payments" in plan.steps[0].sql_hint

    def test_index_removed_hint_is_comment(self):
        c = _change(ChangeType.INDEX_REMOVED, column="idx_email")
        plan = plan_migration([c])
        assert "DROP INDEX" in plan.steps[0].sql_hint
