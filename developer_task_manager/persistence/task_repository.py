from __future__ import annotations

from abc import ABC, abstractmethod

from developer_task_manager.domain import Task


class RepositoryError(RuntimeError):
    """A readable wrapper for storage and data-integrity failures."""


class TaskRepository(ABC):
    @abstractmethod
    def load_all(self) -> list[Task]:
        raise NotImplementedError

    @abstractmethod
    def save_all(self, tasks: list[Task]) -> None:
        raise NotImplementedError

