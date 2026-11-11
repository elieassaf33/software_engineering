from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from developer_task_manager.domain import ContextSnapshot, Task, TaskStatus
from developer_task_manager.persistence import JsonTaskRepository, RepositoryError


def test_save_and_load_round_trip_preserves_fields_and_timestamps(tmp_path) -> None:
    path = tmp_path / "data" / "tasks.json"
    repository = JsonTaskRepository(path)
    created = datetime(2024, 5, 1, 10, 30, tzinfo=timezone.utc)
    modified = datetime(2024, 5, 2, 11, 45, tzinfo=timezone.utc)
    task = Task(
        id="task-123",
        title="Resume parser work",
        context=ContextSnapshot(
            project_name="Compiler",
            file_paths=["src/parser.py"],
            next_action="Fix precedence",
        ),
        notes="Keep the grammar small",
        tags=["parser"],
        status=TaskStatus.PAUSED,
        created_at=created,
        modified_at=modified,
    )

    repository.save_all([task])
    loaded = repository.load_all()

    assert len(loaded) == 1
    assert loaded[0].to_dict() == task.to_dict()
    assert loaded[0].created_at == created
    assert loaded[0].modified_at == modified


def test_missing_json_file_returns_empty_list(tmp_path) -> None:
    assert JsonTaskRepository(tmp_path / "missing.json").load_all() == []


def test_empty_json_file_returns_empty_list(tmp_path) -> None:
    path = tmp_path / "tasks.json"
    path.write_text("", encoding="utf-8")

    assert JsonTaskRepository(path).load_all() == []


def test_malformed_json_reports_error_without_modifying_file(tmp_path) -> None:
    path = tmp_path / "tasks.json"
    original = "{not-json"
    path.write_text(original, encoding="utf-8")

    with pytest.raises(RepositoryError, match="malformed"):
        JsonTaskRepository(path).load_all()

    assert path.read_text(encoding="utf-8") == original


@pytest.mark.parametrize(
    "content",
    [
        "{}",
        '[{"id": "x"}]',
        '[{"id":"x","title":"","context":{},"status":"Planned",'
        '"created_at":"2024-01-01T00:00:00+00:00",'
        '"modified_at":"2024-01-01T00:00:00+00:00"}]',
        '[{"id":"x","title":"A","context":[],"status":"Planned",'
        '"created_at":"2024-01-01T00:00:00+00:00",'
        '"modified_at":"2024-01-01T00:00:00+00:00"}]',
    ],
)
def test_structurally_invalid_data_is_rejected(tmp_path, content: str) -> None:
    path = tmp_path / "tasks.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(RepositoryError):
        JsonTaskRepository(path).load_all()


def test_duplicate_ids_are_rejected(tmp_path) -> None:
    path = tmp_path / "tasks.json"
    task = Task(title="One").to_dict()
    path.write_text(json.dumps([task, task]), encoding="utf-8")

    with pytest.raises(RepositoryError, match="duplicate"):
        JsonTaskRepository(path).load_all()


def test_legacy_format_is_loaded(tmp_path) -> None:
    path = tmp_path / "tasks.json"
    path.write_text(
        json.dumps(
            [{"name": "Legacy", "tool": "VS Code", "notes": "Old", "tags": "one, two",
              "completed": True}]
        ),
        encoding="utf-8",
    )

    task = JsonTaskRepository(path).load_all()[0]

    assert task.title == "Legacy"
    assert task.context.tool == "VS Code"
    assert task.tags == ("one", "two")
    assert task.status == TaskStatus.COMPLETED


def test_save_wraps_file_system_errors(tmp_path) -> None:
    blocking_file = tmp_path / "not-a-directory"
    blocking_file.write_text("x", encoding="utf-8")
    repository = JsonTaskRepository(blocking_file / "tasks.json")

    with pytest.raises(RepositoryError, match="save"):
        repository.save_all([Task(title="Task")])

