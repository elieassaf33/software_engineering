from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from developer_task_manager.domain import ContextSnapshot, Task, TaskStatus

from .task_repository import RepositoryError, TaskRepository


class JsonTaskRepository(TaskRepository):
    """UTF-8 JSON repository with legacy migration and atomic replacement."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load_all(self) -> list[Task]:
        if not self.path.exists():
            return []
        try:
            raw = self.path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RepositoryError(f"Could not read task data: {exc}") from exc
        if not raw.strip():
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RepositoryError(
                f"Task data is malformed JSON at line {exc.lineno}, column {exc.colno}. "
                "The file was left unchanged."
            ) from exc
        if not isinstance(data, list):
            raise RepositoryError("Task data must contain a JSON list. The file was left unchanged.")
        tasks: list[Task] = []
        ids: set[str] = set()
        for index, item in enumerate(data, start=1):
            try:
                task = self._decode_task(item)
            except (ValueError, TypeError) as exc:
                raise RepositoryError(f"Task {index} is structurally invalid: {exc}") from exc
            if task.id in ids:
                raise RepositoryError(f"Task {index} has a duplicate ID: {task.id}")
            ids.add(task.id)
            tasks.append(task)
        return tasks

    def save_all(self, tasks: list[Task]) -> None:
        temporary = self.path.with_name(f".{self.path.name}.{uuid4().hex}.tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(
                [task.to_dict() for task in tasks],
                ensure_ascii=False,
                indent=2,
            )
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except (OSError, TypeError, ValueError) as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise RepositoryError(f"Could not save task data safely: {exc}") from exc

    @staticmethod
    def _decode_task(item: Any) -> Task:
        if not isinstance(item, dict):
            raise ValueError("each entry must be an object")
        if "title" in item:
            return Task.from_dict(item)
        if "name" not in item:
            raise ValueError("missing title")
        # Legacy task_manager.py schema.
        now = datetime.now(timezone.utc)
        completed = item.get("completed", False)
        if not isinstance(completed, bool):
            raise ValueError("legacy completed value must be true or false")
        return Task(
            id=str(uuid4()),
            title=item["name"],
            context=ContextSnapshot(tool=item.get("tool", "")),
            notes=item.get("notes", ""),
            tags=item.get("tags", ""),
            status=TaskStatus.COMPLETED if completed else TaskStatus.PLANNED,
            created_at=now,
            modified_at=now,
        )

