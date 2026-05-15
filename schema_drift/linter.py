"""Lint schema snapshots for common structural issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from schema_drift.snapshot import DatabaseSnapshot


@dataclass
class LintIssue:
    table: str
    column: str | None
    code: str
    message: str
    severity: str  # "warning" | "error"

    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "column": self.column,
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class LintResult:
    snapshot_id: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [i.to_dict() for i in self.issues],
        }


def lint_snapshot(snapshot: DatabaseSnapshot) -> LintResult:
    """Run all lint checks against a snapshot and return a LintResult."""
    issues: List[LintIssue] = []

    for table_name, table in snapshot.tables.items():
        # Check for tables with no columns
        if not table.columns:
            issues.append(LintIssue(
                table=table_name,
                column=None,
                code="L001",
                message="Table has no columns.",
                severity="error",
            ))

        # Check for columns with no type defined
        for col in table.columns:
            if not col.col_type or col.col_type.strip() == "":
                issues.append(LintIssue(
                    table=table_name,
                    column=col.name,
                    code="L002",
                    message=f"Column '{col.name}' has no type defined.",
                    severity="error",
                ))

        # Check for duplicate column names (case-insensitive)
        seen: dict[str, str] = {}
        for col in table.columns:
            key = col.name.lower()
            if key in seen:
                issues.append(LintIssue(
                    table=table_name,
                    column=col.name,
                    code="L003",
                    message=f"Duplicate column name '{col.name}' (case-insensitive).",
                    severity="error",
                ))
            else:
                seen[key] = col.name

        # Warn about nullable columns with no default
        for col in table.columns:
            if col.nullable and col.default is None:
                issues.append(LintIssue(
                    table=table_name,
                    column=col.name,
                    code="L004",
                    message=f"Nullable column '{col.name}' has no default value.",
                    severity="warning",
                ))

    return LintResult(snapshot_id=snapshot.snapshot_id, issues=issues)
