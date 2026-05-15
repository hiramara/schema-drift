"""Tests for schema_drift.deduplicator."""

import pytest

from schema_drift.differ import ChangeType, SchemaChange
from schema_drift.deduplicator import (
    DeduplicationResult,
    deduplicate_changes,
    _change_key,
)


def _change(
    table: str = "users",
    column: str | None = "id",
    change_type: ChangeType = ChangeType.COLUMN_ADDED,
    before: dict | None = None,
    after: dict | None = None,
) -> SchemaChange:
    return SchemaChange(
        table=table,
        column=column,
        change_type=change_type,
        before=before,
        after=after,
    )


class TestDeduplicateChanges:
    def test_empty_list_returns_empty_result(self):
        result = deduplicate_changes([])
        assert result.original_count == 0
        assert result.removed_count == 0
        assert result.deduplicated == []

    def test_no_duplicates_unchanged(self):
        changes = [
            _change(table="users", column="id", change_type=ChangeType.COLUMN_ADDED),
            _change(table="users", column="name", change_type=ChangeType.COLUMN_ADDED),
        ]
        result = deduplicate_changes(changes)
        assert result.original_count == 2
        assert result.removed_count == 0
        assert len(result.deduplicated) == 2

    def test_exact_duplicate_removed(self):
        c = _change()
        result = deduplicate_changes([c, c])
        assert result.original_count == 2
        assert result.removed_count == 1
        assert len(result.deduplicated) == 1

    def test_first_occurrence_preserved(self):
        c1 = _change(column="id")
        c2 = _change(column="id")  # duplicate
        result = deduplicate_changes([c1, c2])
        assert result.deduplicated[0] is c1

    def test_different_tables_not_deduplicated(self):
        c1 = _change(table="users")
        c2 = _change(table="orders")
        result = deduplicate_changes([c1, c2])
        assert result.removed_count == 0

    def test_different_change_types_not_deduplicated(self):
        c1 = _change(change_type=ChangeType.COLUMN_ADDED)
        c2 = _change(change_type=ChangeType.COLUMN_REMOVED)
        result = deduplicate_changes([c1, c2])
        assert result.removed_count == 0

    def test_different_before_after_not_deduplicated(self):
        c1 = _change(
            change_type=ChangeType.COLUMN_MODIFIED,
            before={"type": "int"},
            after={"type": "bigint"},
        )
        c2 = _change(
            change_type=ChangeType.COLUMN_MODIFIED,
            before={"type": "int"},
            after={"type": "text"},
        )
        result = deduplicate_changes([c1, c2])
        assert result.removed_count == 0

    def test_multiple_duplicates_all_removed(self):
        c = _change()
        result = deduplicate_changes([c, c, c, c])
        assert result.removed_count == 3
        assert len(result.deduplicated) == 1

    def test_to_dict_structure(self):
        c = _change()
        result = deduplicate_changes([c, c])
        d = result.to_dict()
        assert d["original_count"] == 2
        assert d["deduplicated_count"] == 1
        assert d["removed_count"] == 1
        assert isinstance(d["changes"], list)
        assert len(d["changes"]) == 1

    def test_change_key_none_column_treated_as_empty_string(self):
        c = _change(column=None)
        key = _change_key(c)
        assert key[1] == ""
