"""Merge two snapshots into a single unified snapshot.

The 'to' snapshot takes precedence for overlapping tables/columns.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from schema_drift.snapshot import DatabaseSnapshot, TableSchema, ColumnSchema


@dataclass
class MergeResult:
    snapshot: DatabaseSnapshot
    added_tables: List[str] = field(default_factory=list)
    overwritten_tables: List[str] = field(default_factory=list)
    kept_tables: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "snapshot": self.snapshot.to_dict(),
            "added_tables": self.added_tables,
            "overwritten_tables": self.overwritten_tables,
            "kept_tables": self.kept_tables,
            "total_tables": len(self.snapshot.tables),
        }


def merge_snapshots(
    base: DatabaseSnapshot,
    override: DatabaseSnapshot,
    merged_id: Optional[str] = None,
    strategy: str = "override",
) -> MergeResult:
    """Merge *override* into *base*.

    Strategies:
        ``override``  – tables present in *override* replace those in *base*.
        ``additive``  – only tables absent from *base* are copied from *override*.

    Args:
        base: The starting snapshot.
        override: The snapshot whose tables take priority (or fill gaps).
        merged_id: Optional explicit snapshot ID for the result.
        strategy: ``'override'`` (default) or ``'additive'``.

    Returns:
        :class:`MergeResult` containing the merged snapshot and a summary.
    """
    if strategy not in ("override", "additive"):
        raise ValueError(f"Unknown merge strategy: {strategy!r}")

    merged_tables: Dict[str, TableSchema] = {}
    added: List[str] = []
    overwritten: List[str] = []
    kept: List[str] = []

    # Seed with base tables
    for name, table in base.tables.items():
        merged_tables[name] = table

    # Apply override tables
    for name, table in override.tables.items():
        if name not in merged_tables:
            merged_tables[name] = table
            added.append(name)
        elif strategy == "override":
            merged_tables[name] = table
            overwritten.append(name)
        else:  # additive – keep base version
            kept.append(name)

    # Tables that existed only in base are implicitly kept
    for name in base.tables:
        if name not in override.tables:
            kept.append(name)

    result_id = merged_id or f"{base.snapshot_id}+{override.snapshot_id}"
    merged_snapshot = DatabaseSnapshot(
        snapshot_id=result_id,
        created_at=override.created_at,
        tables=merged_tables,
    )

    return MergeResult(
        snapshot=merged_snapshot,
        added_tables=added,
        overwritten_tables=overwritten,
        kept_tables=kept,
    )
