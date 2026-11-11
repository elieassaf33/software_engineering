from __future__ import annotations

from typing import Iterable

from developer_task_manager.domain import ContextSnapshot, Task, TaskStatus
from developer_task_manager.persistence.task_repository import TaskRepository


class TaskNotFoundError(LookupError):
    pass


class DuplicateTaskIdError(ValueError):
    pass


class TaskService:
    """Task use cases; persistence is supplied through repository injection."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository
        self._tasks = repository.load_all()
        self._ensure_unique_ids()

    def _ensure_unique_ids(self) -> None:
        ids = [task.id for task in self._tasks]
        if len(ids) != len(set(ids)):
            raise DuplicateTaskIdError("Stored tasks contain duplicate IDs.")

    def list_tasks(
        self,
        *,
        query: str = "",
        status: TaskStatus | str | None = None,
        tag: str = "",
    ) -> list[Task]:
        status_filter = TaskStatus(status) if status else None
        tag_filter = tag.strip().lower()
        return [
            task
            for task in self._tasks
            if task.matches(query)
            and (status_filter is None or task.status == status_filter)
            and (not tag_filter or tag_filter in task.tags)
        ]

    def get_task(self, task_id: str) -> Task:
        for task in self._tasks:
            if task.id == task_id:
                return task
        raise TaskNotFoundError(f"No task exists with ID '{task_id}'.")

    def create_task(
        self,
        *,
        title: str,
        context: ContextSnapshot,
        notes: str = "",
        tags: str | Iterable[str] | None = None,
        status: TaskStatus | str = TaskStatus.PLANNED,
    ) -> Task:
        task = Task(title=title, context=context, notes=notes, tags=tags, status=status)
        if any(existing.id == task.id for existing in self._tasks):
            raise DuplicateTaskIdError(f"Task ID '{task.id}' already exists.")
        self._tasks.append(task)
        try:
            self._repository.save_all(self._tasks)
        except Exception:
            self._tasks.remove(task)
            raise
        return task

    def edit_task(
        self,
        task_id: str,
        *,
        title: str,
        context: ContextSnapshot,
        notes: str = "",
        tags: str | Iterable[str] | None = None,
    ) -> Task:
        task = self.get_task(task_id)
        before = task.to_dict()
        task.edit(title=title, context=context, notes=notes, tags=tags)
        try:
            self._repository.save_all(self._tasks)
        except Exception:
            restored = Task.from_dict(before)
            self._tasks[self._tasks.index(task)] = restored
            raise
        return task

    def change_status(self, task_id: str, status: TaskStatus | str) -> Task:
        task = self.get_task(task_id)
        previous_status, previous_modified = task.status, task.modified_at
        task.change_status(status)
        try:
            self._repository.save_all(self._tasks)
        except Exception:
            task.status, task.modified_at = previous_status, previous_modified
            raise
        return task

    def reopen_task(self, task_id: str) -> Task:
        task = self.get_task(task_id)
        if task.status != TaskStatus.COMPLETED:
            raise ValueError("Only a completed task can be reopened.")
        return self.change_status(task_id, TaskStatus.IN_PROGRESS)

    def delete_task(self, task_id: str) -> None:
        task = self.get_task(task_id)
        index = self._tasks.index(task)
        self._tasks.pop(index)
        try:
            self._repository.save_all(self._tasks)
        except Exception:
            self._tasks.insert(index, task)
            raise

    def available_tags(self) -> list[str]:
        return sorted({tag for task in self._tasks for tag in task.tags})

