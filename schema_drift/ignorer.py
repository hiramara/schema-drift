"""Ignore rules for schema drift detection.

Allows users to suppress known/expected changes so they don't
appear in diffs or trigger notifications.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional

from schema_drift.differ import ChangeType, SchemaChange

_DEFAULT_IGNORE_FILE = ".schema_drift_ignore.json"


@dataclass
class IgnoreRule:
    """A single ignore rule."""
    table: Optional[str] = None          # None means any table
    column: Optional[str] = None         # None means any column
    change_type: Optional[str] = None    # None means any change type
    reason: str = ""

    def matches(self, change: SchemaChange) -> bool:
        """Return True if this rule suppresses *change*."""
        if self.table is not None and change.table != self.table:
            return False
        if self.column is not None and change.column != self.column:
            return False
        if self.change_type is not None and change.change_type.value != self.change_type:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "column": self.column,
            "change_type": self.change_type,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IgnoreRule":
        return cls(
            table=data.get("table"),
            column=data.get("column"),
            change_type=data.get("change_type"),
            reason=data.get("reason", ""),
        )


@dataclass
class IgnoreConfig:
    rules: List[IgnoreRule] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"rules": [r.to_dict() for r in self.rules]}

    @classmethod
    def from_dict(cls, data: dict) -> "IgnoreConfig":
        return cls(rules=[IgnoreRule.from_dict(r) for r in data.get("rules", [])])


def load_ignore_config(path: str = _DEFAULT_IGNORE_FILE) -> IgnoreConfig:
    if not os.path.exists(path):
        return IgnoreConfig()
    with open(path, "r", encoding="utf-8") as fh:
        return IgnoreConfig.from_dict(json.load(fh))


def save_ignore_config(config: IgnoreConfig, path: str = _DEFAULT_IGNORE_FILE) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(config.to_dict(), fh, indent=2)


def apply_ignore(changes: List[SchemaChange], config: IgnoreConfig) -> List[SchemaChange]:
    """Return only the changes that are NOT suppressed by any rule."""
    return [c for c in changes if not any(r.matches(c) for r in config.rules)]
