"""snapshotter.py — Capture live database schema snapshots via SQLAlchemy."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

try:
    from sqlalchemy import create_engine, inspect, text
except ImportError:  # pragma: no cover
    create_engine = None  # type: ignore
    inspect = None  # type: ignore
    text = None  # type: ignore

from schema_drift.snapshot import ColumnSchema, IndexSchema, TableSchema, DatabaseSnapshot


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _capture_columns(inspector, table_name: str) -> list[ColumnSchema]:
    columns = []
    for col in inspector.get_columns(table_name):
        columns.append(
            ColumnSchema(
                name=col["name"],
                data_type=str(col["type"]),
                nullable=col.get("nullable", True),
                default=str(col["default"]) if col.get("default") is not None else None,
            )
        )
    return columns


def _capture_indexes(inspector, table_name: str) -> list[IndexSchema]:
    indexes = []
    for idx in inspector.get_indexes(table_name):
        indexes.append(
            IndexSchema(
                name=idx["name"] or "",
                columns=list(idx.get("column_names") or []),
                unique=bool(idx.get("unique", False)),
            )
        )
    return indexes


def capture_snapshot(
    dsn: str,
    snapshot_id: str,
    tables: Optional[list[str]] = None,
) -> DatabaseSnapshot:
    """Connect to *dsn* and return a :class:`DatabaseSnapshot`.

    Args:
        dsn: SQLAlchemy connection string.
        snapshot_id: Identifier for the resulting snapshot.
        tables: Optional list of table names to include.  If *None*, all
                tables discovered by the inspector are captured.
    """
    if create_engine is None:  # pragma: no cover
        raise RuntimeError("SQLAlchemy is required for capture_snapshot()")

    engine = create_engine(dsn)
    try:
        inspector = inspect(engine)
        all_tables = inspector.get_table_names()
        target = [t for t in all_tables if t in tables] if tables else all_tables

        schema_tables: list[TableSchema] = []
        for table_name in sorted(target):
            schema_tables.append(
                TableSchema(
                    name=table_name,
                    columns=_capture_columns(inspector, table_name),
                    indexes=_capture_indexes(inspector, table_name),
                )
            )
    finally:
        engine.dispose()

    return DatabaseSnapshot(
        snapshot_id=snapshot_id,
        captured_at=_utcnow(),
        tables=schema_tables,
    )
