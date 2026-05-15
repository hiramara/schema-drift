"""Drift severity scorer — assigns a numeric risk score to a ComparisonResult."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from schema_drift.comparator import ComparisonResult
from schema_drift.differ import ChangeType

# Points assigned per change type
_WEIGHTS: dict[ChangeType, int] = {
    ChangeType.COLUMN_REMOVED: 10,
    ChangeType.COLUMN_TYPE_CHANGED: 7,
    ChangeType.COLUMN_ADDED: 3,
    ChangeType.COLUMN_NULLABLE_CHANGED: 4,
    ChangeType.COLUMN_DEFAULT_CHANGED: 2,
    ChangeType.INDEX_REMOVED: 8,
    ChangeType.INDEX_ADDED: 2,
}

_DEFAULT_WEIGHT = 3


@dataclass
class DriftScore:
    total: int
    breakdown: dict[str, int] = field(default_factory=dict)
    risk_level: str = "low"

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "risk_level": self.risk_level,
            "breakdown": self.breakdown,
        }


def _risk_level(score: int) -> str:
    if score == 0:
        return "none"
    if score < 10:
        return "low"
    if score < 25:
        return "medium"
    if score < 50:
        return "high"
    return "critical"


def score_diff(result: ComparisonResult) -> DriftScore:
    """Compute a numeric drift risk score from a ComparisonResult."""
    breakdown: dict[str, int] = {}
    total = 0

    for change in result.changes:
        weight = _WEIGHTS.get(change.change_type, _DEFAULT_WEIGHT)
        key = change.change_type.value
        breakdown[key] = breakdown.get(key, 0) + weight
        total += weight

    return DriftScore(
        total=total,
        breakdown=breakdown,
        risk_level=_risk_level(total),
    )
