from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ContextSnapshot:
    """Development state needed to resume an interrupted task."""

    project_name: str = ""
    tool: str = ""
    git_branch: str = ""
    file_paths: tuple[str, ...] = ()
    last_command: str = ""
    progress_note: str = ""
    next_action: str = ""

    def __post_init__(self) -> None:
        self.project_name = str(self.project_name).strip()
        self.tool = str(self.tool).strip()
        self.git_branch = str(self.git_branch).strip()
        self.file_paths = self._normalize_paths(self.file_paths)
        self.last_command = str(self.last_command).strip()
        self.progress_note = str(self.progress_note).strip()
        self.next_action = str(self.next_action).strip()

    @staticmethod
    def _normalize_paths(paths: Any) -> tuple[str, ...]:
        if paths is None:
            return ()
        if isinstance(paths, str):
            paths = paths.replace("\n", ",").split(",")
        if not isinstance(paths, (list, tuple)):
            raise ValueError("File paths must be a list or comma-separated text.")
        result: list[str] = []
        for path in paths:
            value = str(path).strip()
            if value and value not in result:
                result.append(value)
        return tuple(result)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "tool": self.tool,
            "git_branch": self.git_branch,
            "file_paths": list(self.file_paths),
            "last_command": self.last_command,
            "progress_note": self.progress_note,
            "next_action": self.next_action,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ContextSnapshot":
        if data is None:
            return cls()
        if not isinstance(data, dict):
            raise ValueError("Task context must be a JSON object.")
        return cls(
            project_name=data.get("project_name", ""),
            tool=data.get("tool", ""),
            git_branch=data.get("git_branch", ""),
            file_paths=data.get("file_paths", ()),
            last_command=data.get("last_command", ""),
            progress_note=data.get("progress_note", ""),
            next_action=data.get("next_action", ""),
        )

    def searchable_text(self) -> str:
        return " ".join(
            (
                self.project_name,
                self.tool,
                self.git_branch,
                " ".join(self.file_paths),
                self.last_command,
                self.progress_note,
                self.next_action,
            )
        )

