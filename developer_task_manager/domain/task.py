from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable
from uuid import uuid4

from .context_snapshot import ContextSnapshot


class ValidationError(ValueError):
    """Raised when domain data does not satisfy task rules."""


class InvalidStatusTransition(ValidationError):
    """Raised when a status change is not permitted."""


class TaskStatus(str, Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    PAUSED = "Paused"
    COMPLETED = "Completed"


ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PLANNED: {TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED},
    TaskStatus.IN_PROGRESS: {TaskStatus.PAUSED, TaskStatus.COMPLETED},
    TaskStatus.PAUSED: {TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED},
    TaskStatus.COMPLETED: {TaskStatus.IN_PROGRESS},
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValidationError(f"{field_name} is not a valid ISO timestamp.") from exc
    else:
        raise ValidationError(f"{field_name} is required and must be a timestamp.")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def normalize_tags(tags: str | Iterable[str] | None) -> tuple[str, ...]:
    if tags is None:
        return ()
    if isinstance(tags, str):
        values = tags.split(",")
    else:
        try:
            values = list(tags)
        except TypeError as exc:
            raise ValidationError("Tags must be a list or comma-separated text.") from exc
    normalized: list[str] = []
    seen: set[str] = set()
    for tag in values:
        value = str(tag).strip().lower()
        if value and value not in seen:
            normalized.append(value)
            seen.add(value)
    return tuple(normalized)


@dataclass
class Task:
    title: str
    context: ContextSnapshot = field(default_factory=ContextSnapshot)
    notes: str = ""
    tags: tuple[str, ...] = ()
    status: TaskStatus = TaskStatus.PLANNED
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    modified_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.title = str(self.title).strip()
        if not self.title:
            raise ValidationError("Task title is required.")
        if not isinstance(self.context, ContextSnapshot):
            raise ValidationError("Task context must be a ContextSnapshot.")
        self.notes = str(self.notes).strip()
        self.tags = normalize_tags(self.tags)
        try:
            self.status = TaskStatus(self.status)
        except ValueError as exc:
            raise ValidationError(f"Unknown task status: {self.status}") from exc
        self.id = str(self.id).strip()
        if not self.id:
            raise ValidationError("Task ID is required.")
        self.created_at = parse_timestamp(self.created_at, "Creation timestamp")
        self.modified_at = parse_timestamp(self.modified_at, "Modification timestamp")

    def edit(
        self,
        *,
        title: str,
        context: ContextSnapshot,
        notes: str = "",
        tags: str | Iterable[str] | None = None,
    ) -> None:
        cleaned_title = str(title).strip()
        if not cleaned_title:
            raise ValidationError("Task title is required.")
        if not isinstance(context, ContextSnapshot):
            raise ValidationError("Task context must be a ContextSnapshot.")
        self.title = cleaned_title
        self.context = context
        self.notes = str(notes).strip()
        self.tags = normalize_tags(tags)
        self.modified_at = utc_now()

    def change_status(self, new_status: TaskStatus | str) -> None:
        try:
            target = TaskStatus(new_status)
        except ValueError as exc:
            raise ValidationError(f"Unknown task status: {new_status}") from exc
        if target == self.status:
            return
        if target not in ALLOWED_TRANSITIONS[self.status]:
            raise InvalidStatusTransition(
                f"Cannot change status from {self.status.value} to {target.value}."
            )
        self.status = target
        self.modified_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "context": self.context.to_dict(),
            "notes": self.notes,
            "tags": list(self.tags),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        if not isinstance(data, dict):
            raise ValidationError("Each task must be a JSON object.")
        if "title" not in data:
            raise ValidationError("Task data is missing the title.")
        return cls(
            id=data.get("id", ""),
            title=data["title"],
            context=ContextSnapshot.from_dict(data.get("context")),
            notes=data.get("notes", ""),
            tags=data.get("tags", ()),
            status=data.get("status", TaskStatus.PLANNED.value),
            created_at=data.get("created_at"),
            modified_at=data.get("modified_at"),
        )

    def matches(self, query: str) -> bool:
        query = query.strip().casefold()
        if not query:
            return True
        haystack = " ".join((self.title, self.notes, self.context.searchable_text()))
        return query in haystack.casefold()

