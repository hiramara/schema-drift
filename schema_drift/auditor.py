"""Audit log: records every snapshot save and diff operation with timestamps."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _audit_path(storage_dir: str) -> Path:
    return Path(storage_dir) / "audit_log.json"


@dataclass
class AuditEntry:
    event: str          # e.g. "snapshot_saved", "diff_run", "baseline_set"
    timestamp: str
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event": self.event,
            "timestamp": self.timestamp,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            event=data["event"],
            timestamp=data["timestamp"],
            details=data.get("details", {}),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_entries(storage_dir: str) -> List[AuditEntry]:
    path = _audit_path(storage_dir)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return [AuditEntry.from_dict(e) for e in raw]


def _save_entries(storage_dir: str, entries: List[AuditEntry]) -> None:
    path = _audit_path(storage_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([e.to_dict() for e in entries], fh, indent=2)


def record_event(
    storage_dir: str,
    event: str,
    details: Optional[dict] = None,
) -> AuditEntry:
    entries = _load_entries(storage_dir)
    entry = AuditEntry(event=event, timestamp=_now_iso(), details=details or {})
    entries.append(entry)
    _save_entries(storage_dir, entries)
    return entry


def get_audit_log(storage_dir: str) -> List[AuditEntry]:
    return _load_entries(storage_dir)


def clear_audit_log(storage_dir: str) -> None:
    path = _audit_path(storage_dir)
    if path.exists():
        path.unlink()
