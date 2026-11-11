from datetime import datetime, timezone

import pytest

from developer_task_manager.domain import (
    ContextSnapshot,
    InvalidStatusTransition,
    Task,
    TaskStatus,
    ValidationError,
)


def test_valid_task_creation(context: ContextSnapshot) -> None:
    task = Task(title="Fix expression parser", context=context, tags=["Parser", " urgent "])

    assert task.title == "Fix expression parser"
    assert task.status == TaskStatus.PLANNED
    assert task.tags == ("parser", "urgent")
    assert task.id
    assert task.created_at.tzinfo is not None


def test_empty_title_is_rejected() -> None:
    with pytest.raises(ValidationError, match="title"):
        Task(title="  ")


def test_tags_are_trimmed_lowercase_deduplicated() -> None:
    task = Task(title="Task", tags=" Python, ui, PYTHON, , UI ")

    assert task.tags == ("python", "ui")


def test_valid_status_transitions(context: ContextSnapshot) -> None:
    task = Task(title="Task", context=context)
    task.change_status(TaskStatus.IN_PROGRESS)
    task.change_status(TaskStatus.PAUSED)
    task.change_status(TaskStatus.IN_PROGRESS)
    task.change_status(TaskStatus.COMPLETED)
    task.change_status(TaskStatus.IN_PROGRESS)

    assert task.status == TaskStatus.IN_PROGRESS


def test_invalid_status_transition_is_rejected() -> None:
    task = Task(title="Task")

    with pytest.raises(InvalidStatusTransition):
        task.change_status(TaskStatus.PAUSED)


def test_edit_preserves_id_and_creation_time(context: ContextSnapshot) -> None:
    created = datetime(2025, 1, 2, tzinfo=timezone.utc)
    task = Task(
        id="stable-id",
        title="Old",
        created_at=created,
        modified_at=created,
    )

    task.edit(title="New", context=context, notes="Changed", tags="one, two")

    assert task.id == "stable-id"
    assert task.created_at == created
    assert task.title == "New"
    assert task.modified_at > created


def test_new_tasks_receive_unique_ids() -> None:
    ids = {Task(title=f"Task {index}").id for index in range(100)}

    assert len(ids) == 100

