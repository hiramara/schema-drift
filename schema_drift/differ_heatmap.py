"""Generates a drift heatmap: a table-keyed frequency map of changes over time."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from schema_drift.differ import SchemaChange


@dataclass
class HeatmapCell:
    table: str
    total_changes: int
    by_type: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "total_changes": self.total_changes,
            "by_type": self.by_type,
        }


@dataclass
class DriftHeatmap:
    cells: List[HeatmapCell] = field(default_factory=list)

    # Ordered from hottest (most changes) to coolest.
    def sorted_cells(self) -> List[HeatmapCell]:
        return sorted(self.cells, key=lambda c: c.total_changes, reverse=True)

    def hottest_table(self) -> str | None:
        if not self.cells:
            return None
        return self.sorted_cells()[0].table

    def total_changes(self) -> int:
        return sum(c.total_changes for c in self.cells)

    def to_dict(self) -> dict:
        return {
            "total_changes": self.total_changes(),
            "hottest_table": self.hottest_table(),
            "cells": [c.to_dict() for c in self.sorted_cells()],
        }


def build_heatmap(change_sets: Sequence[Sequence[SchemaChange]]) -> DriftHeatmap:
    """Aggregate multiple diff result lists into a single drift heatmap.

    Args:
        change_sets: An ordered sequence of change lists (e.g. one per diff run).

    Returns:
        A DriftHeatmap summarising change frequency per table.
    """
    accumulator: Dict[str, Dict[str, int]] = {}

    for changes in change_sets:
        for change in changes:
            table = change.table
            change_type = change.change_type.value
            if table not in accumulator:
                accumulator[table] = {}
            accumulator[table][change_type] = (
                accumulator[table].get(change_type, 0) + 1
            )

    cells = [
        HeatmapCell(
            table=table,
            total_changes=sum(counts.values()),
            by_type=dict(counts),
        )
        for table, counts in accumulator.items()
    ]

    return DriftHeatmap(cells=cells)
