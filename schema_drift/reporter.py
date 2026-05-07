"""HTML and Markdown report generation for schema diffs."""

from __future__ import annotations

from typing import List

from schema_drift.changelog import changelog_to_dict
from schema_drift.differ import SchemaChange, ChangeType
from schema_drift.snapshot import DatabaseSnapshot


_CHANGE_EMOJI = {
    ChangeType.ADDED: "✅",
    ChangeType.REMOVED: "❌",
    ChangeType.MODIFIED: "✏️",
}


def generate_markdown_report(
    changes: List[SchemaChange],
    old_snapshot: DatabaseSnapshot,
    new_snapshot: DatabaseSnapshot,
) -> str:
    """Return a Markdown-formatted diff report."""
    lines: List[str] = []
    lines.append("# Schema Drift Report")
    lines.append("")
    lines.append(f"**From:** `{old_snapshot.snapshot_id}`  ")
    lines.append(f"**To:** `{new_snapshot.snapshot_id}`")
    lines.append("")

    if not changes:
        lines.append("_No schema changes detected._")
        return "\n".join(lines)

    lines.append(f"## Summary — {len(changes)} change(s)")
    lines.append("")
    lines.append("| # | Type | Table | Object | Detail |")
    lines.append("|---|------|-------|--------|--------|")

    for i, change in enumerate(changes, start=1):
        emoji = _CHANGE_EMOJI.get(change.change_type, "")
        label = f"{emoji} {change.change_type.value}"
        detail = change.detail or ""
        lines.append(
            f"| {i} | {label} | `{change.table}` | `{change.object_name}` | {detail} |"
        )

    lines.append("")
    return "\n".join(lines)


def generate_html_report(
    changes: List[SchemaChange],
    old_snapshot: DatabaseSnapshot,
    new_snapshot: DatabaseSnapshot,
) -> str:
    """Return a minimal HTML-formatted diff report."""
    data = changelog_to_dict(changes, old_snapshot, new_snapshot)
    rows_html = ""

    for entry in data.get("changes", []):
        change_type = entry.get("change_type", "")
        css_class = {
            ChangeType.ADDED.value: "added",
            ChangeType.REMOVED.value: "removed",
            ChangeType.MODIFIED.value: "modified",
        }.get(change_type, "")
        rows_html += (
            f'<tr class="{css_class}">'
            f'<td>{change_type}</td>'
            f'<td>{entry.get("table", "")}</td>'
            f'<td>{entry.get("object_name", "")}</td>'
            f'<td>{entry.get("detail", "")}</td>'
            f"</tr>\n"
        )

    no_changes_row = (
        '<tr><td colspan="4"><em>No schema changes detected.</em></td></tr>'
        if not changes
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Schema Drift Report</title>
<style>
  body {{ font-family: sans-serif; padding: 1rem; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.8rem; text-align: left; }}
  .added {{ background: #e6ffed; }}
  .removed {{ background: #ffeef0; }}
  .modified {{ background: #fff8c5; }}
</style></head>
<body>
<h1>Schema Drift Report</h1>
<p><strong>From:</strong> <code>{data['old_snapshot_id']}</code> &rarr;
   <strong>To:</strong> <code>{data['new_snapshot_id']}</code></p>
<table>
  <thead><tr><th>Type</th><th>Table</th><th>Object</th><th>Detail</th></tr></thead>
  <tbody>{rows_html}{no_changes_row}</tbody>
</table>
</body></html>
"""
