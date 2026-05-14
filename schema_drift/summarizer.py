"""Summarize schema drift statistics across snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from schema_drift.differ import SchemaChange, ChangeType
from schema_drift.comparator import ComparisonResult


@dataclass
class DriftSummary:
    from_id: str
    to_id: str
    total_changes: int
    by_type: Dict[str, int] = field(default_factory=dict)
    by_table: Dict[str, int] = field(default_factory=dict)
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    def to_dict(self) -> dict:
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "total_changes": self.total_changes,
            "by_type": self.by_type,
            "by_table": self.by_table,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
        }


_CRITICAL_TYPES = {ChangeType.COLUMN_REMOVED, ChangeType.INDEX_REMOVED}
_WARNING_TYPES = {ChangeType.COLUMN_MODIFIED}


def _severity_bucket(change: SchemaChange) -> str:
    if change.change_type in _CRITICAL_TYPES:
        return "critical"
    if change.change_type in _WARNING_TYPES:
        return "warning"
    return "info"


def summarize(result: ComparisonResult) -> DriftSummary:
    """Build a DriftSummary from a ComparisonResult."""
    changes: List[SchemaChange] = result.changes
    by_type: Dict[str, int] = {}
    by_table: Dict[str, int] = {}
    critical = warning = info = 0

    for change in changes:
        type_key = change.change_type.value
        by_type[type_key] = by_type.get(type_key, 0) + 1
        by_table[change.table] = by_table.get(change.table, 0) + 1

        bucket = _severity_bucket(change)
        if bucket == "critical":
            critical += 1
        elif bucket == "warning":
            warning += 1
        else:
            info += 1

    return DriftSummary(
        from_id=result.from_snapshot.snapshot_id,
        to_id=result.to_snapshot.snapshot_id,
        total_changes=len(changes),
        by_type=by_type,
        by_table=by_table,
        critical_count=critical,
        warning_count=warning,
        info_count=info,
    )
