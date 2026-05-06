"""Tests for schema_drift.changelog module."""

import json
import pytest

from schema_drift.differ import SchemaChange, ChangeType
from schema_drift.changelog import generate_changelog, changelog_to_dict, CHANGELOG_VERSION


def make_change(
    change_type: ChangeType,
    object_type: str,
    object_name: str,
    table_name: str | None = None,
    old_value=None,
    new_value=None,
) -> SchemaChange:
    return SchemaChange(
        change_type=change_type,
        object_type=object_type,
        object_name=object_name,
        table_name=table_name,
        old_value=old_value,
        new_value=new_value,
    )


class TestGenerateChangelog:
    def test_empty_changes_returns_no_changes_message(self):
        result = generate_changelog([])
        assert "No schema changes detected" in result
        assert CHANGELOG_VERSION in result

    def test_header_contains_snapshot_ids(self):
        result = generate_changelog([], from_snapshot_id="snap-001", to_snapshot_id="snap-002")
        assert "snap-001" in result
        assert "snap-002" in result

    def test_added_column_appears_with_plus_prefix(self):
        change = make_change(ChangeType.ADDED, "column", "email", table_name="users")
        result = generate_changelog([change])
        assert "[+]" in result
        assert "users.email" in result

    def test_removed_column_appears_with_minus_prefix(self):
        change = make_change(ChangeType.REMOVED, "column", "legacy_id", table_name="orders")
        result = generate_changelog([change])
        assert "[-]" in result
        assert "orders.legacy_id" in result

    def test_modified_column_shows_before_and_after(self):
        change = make_change(
            ChangeType.MODIFIED,
            "column",
            "age",
            table_name="users",
            old_value={"type": "INTEGER"},
            new_value={"type": "BIGINT"},
        )
        result = generate_changelog([change])
        assert "[~]" in result
        assert "before:" in result
        assert "after:" in result
        assert "INTEGER" in result
        assert "BIGINT" in result

    def test_changes_grouped_by_table(self):
        changes = [
            make_change(ChangeType.ADDED, "column", "col1", table_name="alpha"),
            make_change(ChangeType.REMOVED, "column", "col2", table_name="beta"),
            make_change(ChangeType.ADDED, "column", "col3", table_name="alpha"),
        ]
        result = generate_changelog(changes)
        alpha_pos = result.index("## Table: alpha")
        beta_pos = result.index("## Table: beta")
        assert alpha_pos < beta_pos  # sorted alphabetically
        assert result.count("## Table:") == 2

    def test_total_changes_count_in_header(self):
        changes = [
            make_change(ChangeType.ADDED, "column", "a", table_name="t"),
            make_change(ChangeType.REMOVED, "column", "b", table_name="t"),
        ]
        result = generate_changelog(changes)
        assert "Total changes: 2" in result


class TestChangelogToDict:
    def test_returns_correct_version(self):
        result = changelog_to_dict([])
        assert result["version"] == CHANGELOG_VERSION

    def test_snapshot_ids_preserved(self):
        result = changelog_to_dict([], from_snapshot_id="A", to_snapshot_id="B")
        assert result["from_snapshot"] == "A"
        assert result["to_snapshot"] == "B"

    def test_changes_serialized(self):
        change = make_change(ChangeType.ADDED, "column", "email", table_name="users")
        result = changelog_to_dict([change])
        assert result["total_changes"] == 1
        assert isinstance(result["changes"], list)
        assert result["changes"][0]["object_name"] == "email"

    def test_is_json_serializable(self):
        change = make_change(ChangeType.MODIFIED, "column", "price", table_name="products",
                             old_value={"type": "FLOAT"}, new_value={"type": "DECIMAL"})
        result = changelog_to_dict([change], from_snapshot_id="s1", to_snapshot_id="s2")
        dumped = json.dumps(result)  # should not raise
        assert "price" in dumped
