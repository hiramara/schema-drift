"""Filter schema changes by table, change type, or severity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Set

from .differ import SchemaChange, ChangeType
from .notifier import _change_severity


@dataclass
class FilterConfig:
    tables: Optional[Set[str]] = None          # None means all tables
    change_types: Optional[Set[ChangeType]] = None  # None means all types
    min_severity: Optional[str] = None         # 'low', 'medium', 'critical'
    exclude_tables: Set[str] = field(default_factory=set)

    @classmethod
    def from_dict(cls, data: dict) -> "FilterConfig":
        tables = set(data["tables"]) if data.get("tables") else None
        change_types = (
            {ChangeType(ct) for ct in data["change_types"]}
            if data.get("change_types")
            else None
        )
        return cls(
            tables=tables,
            change_types=change_types,
            min_severity=data.get("min_severity"),
            exclude_tables=set(data.get("exclude_tables", [])),
        )

    def to_dict(self) -> dict:
        return {
            "tables": sorted(self.tables) if self.tables is not None else None,
            "change_types": (
                sorted(ct.value for ct in self.change_types)
                if self.change_types is not None
                else None
            ),
            "min_severity": self.min_severity,
            "exclude_tables": sorted(self.exclude_tables),
        }


_SEVERITY_ORDER = ["low", "medium", "critical"]


def _severity_rank(severity: str) -> int:
    try:
        return _SEVERITY_ORDER.index(severity)
    except ValueError:
        return 0


def apply_filter(changes: List[SchemaChange], cfg: FilterConfig) -> List[SchemaChange]:
    """Return only the changes that pass all active filter criteria."""
    result = []
    min_rank = _severity_rank(cfg.min_severity) if cfg.min_severity else 0

    for change in changes:
        if cfg.exclude_tables and change.table in cfg.exclude_tables:
            continue
        if cfg.tables is not None and change.table not in cfg.tables:
            continue
        if cfg.change_types is not None and change.change_type not in cfg.change_types:
            continue
        if cfg.min_severity is not None:
            rank = _severity_rank(_change_severity(change))
            if rank < min_rank:
                continue
        result.append(change)

    return result
