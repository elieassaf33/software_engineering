from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from developer_task_manager.domain import ContextSnapshot  # noqa: E402


@pytest.fixture
def context() -> ContextSnapshot:
    return ContextSnapshot(
        project_name="Compiler",
        tool="PyCharm",
        git_branch="feature/parser",
        file_paths=["src/parser.py", "tests/test_parser.py"],
        last_command="pytest tests/test_parser.py",
        progress_note="One precedence test is failing.",
        next_action="Inspect operator binding.",
    )

