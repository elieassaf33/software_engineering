from __future__ import annotations

import pytest

from developer_task_manager.application import TaskNotFoundError, TaskService
from developer_task_manager.domain import ContextSnapshot, TaskStatus
from developer_task_manager.persistence import RepositoryError, TaskRepository


class MemoryRepository(TaskRepository):
    def __init__(self) -> None:
        self.tasks = []
        self.fail_saves = False

    def load_all(self):
        return list(self.tasks)

    def save_all(self, tasks):
        if self.fail_saves:
            raise RepositoryError("disk unavailable")
        self.tasks = list(tasks)


def test_create_edit_and_delete(context: ContextSnapshot) -> None:
    repository = MemoryRepository()
    service = TaskService(repository)
    task = service.create_task(title="Original", context=context, tags="backend")

    edited = service.edit_task(
        task.id,
        title="Edited",
        context=ContextSnapshot(project_name="New project"),
        notes="Updated",
        tags=["updated"],
    )
    assert edited.title == "Edited"
    assert repository.tasks[0].notes == "Updated"

    service.delete_task(task.id)
    assert service.list_tasks() == []
    with pytest.raises(TaskNotFoundError):
        service.get_task(task.id)


def test_searches_title_notes_and_context(context: ContextSnapshot) -> None:
    service = TaskService(MemoryRepository())
    service.create_task(title="Parser bug", context=context, notes="Reported by QA", tags="bug")
    service.create_task(
        title="Write guide",
        context=ContextSnapshot(project_name="Documentation"),
        notes="User manual",
        tags="docs",
    )

    assert len(service.list_tasks(query="precedence")) == 1
    assert len(service.list_tasks(query="qa")) == 1
    assert len(service.list_tasks(query="parser bug")) == 1
    assert service.list_tasks(query="missing") == []


def test_filters_by_status_and_tag(context: ContextSnapshot) -> None:
    service = TaskService(MemoryRepository())
    first = service.create_task(title="First", context=context, tags="bug, urgent")
    service.create_task(title="Second", context=context, tags="docs")
    service.change_status(first.id, TaskStatus.IN_PROGRESS)

    assert [task.id for task in service.list_tasks(status="In Progress")] == [first.id]
    assert [task.id for task in service.list_tasks(tag="urgent")] == [first.id]


def test_reopens_completed_task(context: ContextSnapshot) -> None:
    service = TaskService(MemoryRepository())
    task = service.create_task(title="Task", context=context)
    service.change_status(task.id, TaskStatus.COMPLETED)

    service.reopen_task(task.id)

    assert task.status == TaskStatus.IN_PROGRESS


def test_repository_save_error_rolls_back_create(context: ContextSnapshot) -> None:
    repository = MemoryRepository()
    service = TaskService(repository)
    repository.fail_saves = True

    with pytest.raises(RepositoryError):
        service.create_task(title="Unsaved", context=context)

    assert service.list_tasks() == []


def test_invalid_id_operations_are_handled() -> None:
    service = TaskService(MemoryRepository())

    with pytest.raises(TaskNotFoundError, match="missing"):
        service.delete_task("missing")

