"""Notification module for schema drift alerts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from schema_drift.comparator import ComparisonResult
from schema_drift.differ import ChangeType


@dataclass
class NotificationConfig:
    """Configuration for drift notifications."""
    min_severity: str = "info"  # info | warning | critical
    include_tables: List[str] = field(default_factory=list)  # empty = all tables
    exclude_tables: List[str] = field(default_factory=list)

    _SEVERITY_RANK = {"info": 0, "warning": 1, "critical": 2}

    def severity_rank(self) -> int:
        return self._SEVERITY_RANK.get(self.min_severity, 0)


def _change_severity(change_type: ChangeType) -> str:
    """Map a ChangeType to a severity level."""
    if change_type in (ChangeType.COLUMN_REMOVED, ChangeType.INDEX_REMOVED):
        return "critical"
    if change_type in (ChangeType.COLUMN_MODIFIED, ChangeType.INDEX_MODIFIED):
        return "warning"
    return "info"


@dataclass
class DriftNotification:
    """A notification payload summarising detected drift."""
    from_snapshot_id: str
    to_snapshot_id: str
    total_changes: int
    critical: int
    warning: int
    info: int
    summary_lines: List[str]

    def as_text(self) -> str:
        lines = [
            f"Schema drift detected: {self.from_snapshot_id} -> {self.to_snapshot_id}",
            f"Changes: {self.total_changes} total "
            f"(critical={self.critical}, warning={self.warning}, info={self.info})",
            "",
        ] + self.summary_lines
        return "\n".join(lines)


def build_notification(
    result: ComparisonResult,
    config: Optional[NotificationConfig] = None,
) -> Optional[DriftNotification]:
    """Build a DriftNotification from a ComparisonResult.

    Returns None when no changes meet the configured severity threshold.
    """
    cfg = config or NotificationConfig()
    rank = cfg.severity_rank()

    counts = {"critical": 0, "warning": 0, "info": 0}
    lines: List[str] = []

    for change in result.changes:
        table = change.table_name
        if cfg.include_tables and table not in cfg.include_tables:
            continue
        if table in cfg.exclude_tables:
            continue

        sev = _change_severity(change.change_type)
        if NotificationConfig._SEVERITY_RANK[sev] < rank:
            continue

        counts[sev] += 1
        lines.append(f"  [{sev.upper()}] {table}: {change.change_type.value} — {change.object_name}")

    total = sum(counts.values())
    if total == 0:
        return None

    return DriftNotification(
        from_snapshot_id=result.from_snapshot_id,
        to_snapshot_id=result.to_snapshot_id,
        total_changes=total,
        critical=counts["critical"],
        warning=counts["warning"],
        info=counts["info"],
        summary_lines=lines,
    )
