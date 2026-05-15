"""Group schema changes by table, change type, or severity for reporting."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

from schema_drift.differ import SchemaChange
from schema_drift.notifier import _change_severity


@dataclass
class ChangeGroup:
    key: str
    changes: List[SchemaChange] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "count": len(self.changes),
            "changes": [c.to_dict() for c in self.changes],
        }


def group_by_table(changes: List[SchemaChange]) -> Dict[str, ChangeGroup]:
    """Return changes bucketed by table name."""
    buckets: Dict[str, ChangeGroup] = defaultdict(lambda: ChangeGroup(key=""))
    for change in changes:
        key = change.table
        if buckets[key].key == "":
            buckets[key].key = key
        buckets[key].changes.append(change)
    return dict(buckets)


def group_by_change_type(changes: List[SchemaChange]) -> Dict[str, ChangeGroup]:
    """Return changes bucketed by ChangeType value."""
    buckets: Dict[str, ChangeGroup] = defaultdict(lambda: ChangeGroup(key=""))
    for change in changes:
        key = change.change_type.value
        if buckets[key].key == "":
            buckets[key].key = key
        buckets[key].changes.append(change)
    return dict(buckets)


def group_by_severity(changes: List[SchemaChange]) -> Dict[str, ChangeGroup]:
    """Return changes bucketed by severity (critical / warning / info)."""
    buckets: Dict[str, ChangeGroup] = defaultdict(lambda: ChangeGroup(key=""))
    for change in changes:
        key = _change_severity(change)
        if buckets[key].key == "":
            buckets[key].key = key
        buckets[key].changes.append(change)
    return dict(buckets)


def groups_to_dict(groups: Dict[str, ChangeGroup]) -> dict:
    """Serialise a mapping of ChangeGroups to a plain dict."""
    return {k: v.to_dict() for k, v in groups.items()}
