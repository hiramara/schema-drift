"""Tests for schema_drift.snapshotter — live schema capture."""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy", reason="SQLAlchemy not installed")

from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
)

from schema_drift.snapshotter import capture_snapshot
from schema_drift.snapshot import DatabaseSnapshot


@pytest.fixture()
def sqlite_engine(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    meta = MetaData()
    Table(
        "users",
        meta,
        Column("id", Integer, primary_key=True),
        Column("email", String(255), nullable=False),
        Column("name", String(100), nullable=True),
        UniqueConstraint("email", name="uq_users_email"),
    )
    Table(
        "posts",
        meta,
        Column("id", Integer, primary_key=True),
        Column("title", String(200), nullable=False),
    )
    meta.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def dsn(sqlite_engine):
    return str(sqlite_engine.url)


class TestCaptureSnapshot:
    def test_returns_database_snapshot(self, dsn):
        result = capture_snapshot(dsn, "snap-1")
        assert isinstance(result, DatabaseSnapshot)

    def test_snapshot_id_preserved(self, dsn):
        result = capture_snapshot(dsn, "my-snap")
        assert result.snapshot_id == "my-snap"

    def test_captured_at_is_set(self, dsn):
        result = capture_snapshot(dsn, "snap-1")
        assert result.captured_at

    def test_all_tables_captured(self, dsn):
        result = capture_snapshot(dsn, "snap-1")
        names = {t.name for t in result.tables}
        assert names == {"users", "posts"}

    def test_table_filter_respected(self, dsn):
        result = capture_snapshot(dsn, "snap-1", tables=["users"])
        assert len(result.tables) == 1
        assert result.tables[0].name == "users"

    def test_columns_captured(self, dsn):
        result = capture_snapshot(dsn, "snap-1", tables=["users"])
        col_names = {c.name for c in result.tables[0].columns}
        assert {"id", "email", "name"}.issubset(col_names)

    def test_nullable_flag(self, dsn):
        result = capture_snapshot(dsn, "snap-1", tables=["users"])
        col_map = {c.name: c for c in result.tables[0].columns}
        assert col_map["name"].nullable is True
        assert col_map["email"].nullable is False

    def test_unique_index_captured(self, dsn):
        result = capture_snapshot(dsn, "snap-1", tables=["users"])
        unique_indexes = [i for i in result.tables[0].indexes if i.unique]
        assert any("email" in i.columns for i in unique_indexes)

    def test_invalid_dsn_raises(self):
        with pytest.raises(Exception):
            capture_snapshot("sqlite:////nonexistent/path/db.sqlite3", "snap-x")
