"""Tests for schema_drift.annotator and cli_annotate."""
from __future__ import annotations

import argparse
import pytest

from schema_drift import annotator
from schema_drift.cli_annotate import (
    cmd_annotation_add,
    cmd_annotation_clear,
    cmd_annotation_list,
    cmd_annotation_remove,
)


@pytest.fixture()
def storage(tmp_path):
    return str(tmp_path)


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"storage": "/tmp", "snapshot_id": "snap-1", "note": "hello"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# annotator unit tests
# ---------------------------------------------------------------------------

class TestAddAnnotation:
    def test_adds_single_note(self, storage):
        annotator.add_annotation(storage, "snap-1", "first note")
        assert annotator.get_annotations(storage, "snap-1") == ["first note"]

    def test_duplicate_not_doubled(self, storage):
        annotator.add_annotation(storage, "snap-1", "dup")
        annotator.add_annotation(storage, "snap-1", "dup")
        assert annotator.get_annotations(storage, "snap-1").count("dup") == 1

    def test_multiple_notes_stored(self, storage):
        annotator.add_annotation(storage, "snap-1", "a")
        annotator.add_annotation(storage, "snap-1", "b")
        notes = annotator.get_annotations(storage, "snap-1")
        assert "a" in notes and "b" in notes

    def test_different_snapshots_isolated(self, storage):
        annotator.add_annotation(storage, "snap-1", "note")
        assert annotator.get_annotations(storage, "snap-2") == []


class TestRemoveAnnotation:
    def test_removes_existing_note(self, storage):
        annotator.add_annotation(storage, "snap-1", "to-remove")
        result = annotator.remove_annotation(storage, "snap-1", "to-remove")
        assert result is True
        assert "to-remove" not in annotator.get_annotations(storage, "snap-1")

    def test_returns_false_for_missing_note(self, storage):
        result = annotator.remove_annotation(storage, "snap-1", "ghost")
        assert result is False


class TestClearAnnotations:
    def test_clear_single_snapshot(self, storage):
        annotator.add_annotation(storage, "snap-1", "x")
        annotator.add_annotation(storage, "snap-2", "y")
        annotator.clear_annotations(storage, "snap-1")
        assert annotator.get_annotations(storage, "snap-1") == []
        assert annotator.get_annotations(storage, "snap-2") == ["y"]

    def test_clear_all(self, storage):
        annotator.add_annotation(storage, "snap-1", "x")
        annotator.add_annotation(storage, "snap-2", "y")
        annotator.clear_annotations(storage)
        assert annotator.all_annotations(storage) == {}


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------

class TestCmdAnnotationAdd:
    def test_returns_0(self, storage):
        args = _args(storage=storage)
        assert cmd_annotation_add(args) == 0

    def test_note_persisted(self, storage):
        args = _args(storage=storage, snapshot_id="s1", note="my note")
        cmd_annotation_add(args)
        assert "my note" in annotator.get_annotations(storage, "s1")


class TestCmdAnnotationRemove:
    def test_returns_1_when_not_found(self, storage):
        args = _args(storage=storage, snapshot_id="s1", note="ghost")
        assert cmd_annotation_remove(args) == 1

    def test_returns_0_on_success(self, storage):
        annotator.add_annotation(storage, "s1", "bye")
        args = _args(storage=storage, snapshot_id="s1", note="bye")
        assert cmd_annotation_remove(args) == 0


class TestCmdAnnotationList:
    def test_returns_0_empty(self, storage):
        args = _args(storage=storage, snapshot_id="empty")
        assert cmd_annotation_list(args) == 0

    def test_returns_0_with_notes(self, storage, capsys):
        annotator.add_annotation(storage, "s1", "visible")
        args = _args(storage=storage, snapshot_id="s1")
        cmd_annotation_list(args)
        out = capsys.readouterr().out
        assert "visible" in out
