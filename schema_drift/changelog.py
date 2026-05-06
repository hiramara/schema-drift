"""Generates a human-readable, diffable changelog from schema changes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

from schema_drift.differ import SchemaChange, ChangeType


CHANGELOG_VERSION = "1.0"


def _format_change(change: SchemaChange) -> str:
    """Format a single SchemaChange into a human-readable line."""
    prefix = {
        ChangeType.ADDED: "[+]",
        ChangeType.REMOVED: "[-]",
        ChangeType.MODIFIED: "[~]",
    }[change.change_type]

    parts = [f"{prefix} {change.object_type.upper()} `{change.object_name}`"]

    if change.table_name:
        parts[0] = f"{prefix} {change.object_type.upper()} `{change.table_name}.{change.object_name}`"

    if change.change_type == ChangeType.MODIFIED and change.old_value and change.new_value:
        parts.append(f"  before: {json.dumps(change.old_value)}")
        parts.append(f"  after:  {json.dumps(change.new_value)}")

    return "\n".join(parts)


def generate_changelog(
    changes: List[SchemaChange],
    from_snapshot_id: Optional[str] = None,
    to_snapshot_id: Optional[str] = None,
) -> str:
    """Render a diffable changelog string from a list of SchemaChange objects."""
    timestamp = datetime.now(timezone.utc).isoformat()
    header_lines = [
        f"# Schema Drift Changelog (v{CHANGELOG_VERSION})",
        f"# Generated: {timestamp}",
    ]
    if from_snapshot_id:
        header_lines.append(f"# From snapshot: {from_snapshot_id}")
    if to_snapshot_id:
        header_lines.append(f"# To snapshot:   {to_snapshot_id}")

    if not changes:
        header_lines.append("# No schema changes detected.")
        return "\n".join(header_lines) + "\n"

    header_lines.append(f"# Total changes: {len(changes)}")

    # Group changes by table
    by_table: dict[str, list[SchemaChange]] = {}
    for change in changes:
        key = change.table_name or "(database-level)"
        by_table.setdefault(key, []).append(change)

    body_lines: list[str] = []
    for table, table_changes in sorted(by_table.items()):
        body_lines.append(f"\n## Table: {table}")
        for change in table_changes:
            body_lines.append(_format_change(change))

    return "\n".join(header_lines) + "\n" + "\n".join(body_lines) + "\n"


def changelog_to_dict(
    changes: List[SchemaChange],
    from_snapshot_id: Optional[str] = None,
    to_snapshot_id: Optional[str] = None,
) -> dict:
    """Serialize changelog metadata and changes to a JSON-compatible dict."""
    return {
        "version": CHANGELOG_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "from_snapshot": from_snapshot_id,
        "to_snapshot": to_snapshot_id,
        "total_changes": len(changes),
        "changes": [c.to_dict() for c in changes],
    }
