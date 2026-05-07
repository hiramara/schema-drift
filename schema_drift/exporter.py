"""Export schema snapshots and diffs to various file formats (JSON, CSV, Markdown)."""

from __future__ import annotations

import csv
import io
import json
from typing import List

from schema_drift.changelog import changelog_to_dict, generate_changelog
from schema_drift.differ import SchemaChange
from schema_drift.reporter import generate_markdown_report
from schema_drift.snapshot import DatabaseSnapshot


def export_snapshot_json(snapshot: DatabaseSnapshot, indent: int = 2) -> str:
    """Serialize a snapshot to a JSON string."""
    return json.dumps(snapshot.to_dict(), indent=indent)


def export_diff_json(
    old: DatabaseSnapshot,
    new: DatabaseSnapshot,
    changes: List[SchemaChange],
    indent: int = 2,
) -> str:
    """Serialize a diff (old snapshot, new snapshot, changes) to a JSON string."""
    payload = {
        "old_snapshot_id": old.snapshot_id,
        "new_snapshot_id": new.snapshot_id,
        "changelog": changelog_to_dict(old, new, changes),
    }
    return json.dumps(payload, indent=indent)


def export_diff_csv(changes: List[SchemaChange]) -> str:
    """Serialize schema changes to CSV format.

    Columns: table, change_type, object_type, name, detail
    """
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["table", "change_type", "object_type", "name", "detail"],
        lineterminator="\n",
    )
    writer.writeheader()
    for change in changes:
        d = change.to_dict()
        writer.writerow(
            {
                "table": d.get("table", ""),
                "change_type": d.get("change_type", ""),
                "object_type": d.get("object_type", ""),
                "name": d.get("name", ""),
                "detail": d.get("detail", ""),
            }
        )
    return output.getvalue()


def export_diff_markdown(
    old: DatabaseSnapshot,
    new: DatabaseSnapshot,
    changes: List[SchemaChange],
) -> str:
    """Serialize a diff to a Markdown report string."""
    return generate_markdown_report(old, new, changes)


EXPORT_FORMATS = {
    "json": export_diff_json,
    "csv": lambda old, new, changes: export_diff_csv(changes),
    "markdown": export_diff_markdown,
}


def export_diff(old: DatabaseSnapshot, new: DatabaseSnapshot, changes: List[SchemaChange], fmt: str) -> str:
    """Export a diff using the named format. Raises ValueError for unknown formats."""
    if fmt not in EXPORT_FORMATS:
        raise ValueError(f"Unknown export format '{fmt}'. Choose from: {sorted(EXPORT_FORMATS)}.")
    return EXPORT_FORMATS[fmt](old, new, changes)
