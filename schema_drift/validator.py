"""Validates a database snapshot against a set of rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from schema_drift.snapshot import DatabaseSnapshot


@dataclass
class ValidationIssue:
    table: str
    column: Optional[str]
    rule: str
    message: str

    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "column": self.column,
            "rule": self.rule,
            "message": self.message,
        }


@dataclass
class ValidationResult:
    snapshot_id: str
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "has_issues": self.has_issues,
            "issue_count": self.issue_count,
            "issues": [i.to_dict() for i in self.issues],
        }


def _check_no_nullable_primary_keys(snap: DatabaseSnapshot) -> List[ValidationIssue]:
    issues = []
    for table_name, table in snap.tables.items():
        for col in table.columns:
            if col.primary_key and col.nullable:
                issues.append(ValidationIssue(
                    table=table_name,
                    column=col.name,
                    rule="no_nullable_primary_keys",
                    message=f"Column '{col.name}' is a primary key but is nullable.",
                ))
    return issues


def _check_no_unnamed_indexes(snap: DatabaseSnapshot) -> List[ValidationIssue]:
    issues = []
    for table_name, table in snap.tables.items():
        for idx in table.indexes:
            if not idx.name or not idx.name.strip():
                issues.append(ValidationIssue(
                    table=table_name,
                    column=None,
                    rule="no_unnamed_indexes",
                    message=f"Table '{table_name}' has an index with an empty or missing name.",
                ))
    return issues


def _check_no_tables_without_primary_key(snap: DatabaseSnapshot) -> List[ValidationIssue]:
    issues = []
    for table_name, table in snap.tables.items():
        has_pk = any(col.primary_key for col in table.columns)
        if not has_pk:
            issues.append(ValidationIssue(
                table=table_name,
                column=None,
                rule="no_tables_without_primary_key",
                message=f"Table '{table_name}' has no primary key column.",
            ))
    return issues


_RULES = [
    _check_no_nullable_primary_keys,
    _check_no_unnamed_indexes,
    _check_no_tables_without_primary_key,
]


def validate_snapshot(snap: DatabaseSnapshot) -> ValidationResult:
    """Run all built-in validation rules against *snap*."""
    result = ValidationResult(snapshot_id=snap.snapshot_id)
    for rule_fn in _RULES:
        result.issues.extend(rule_fn(snap))
    return result
