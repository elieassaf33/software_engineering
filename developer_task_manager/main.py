from __future__ import annotations

import tkinter as tk
from pathlib import Path

from developer_task_manager.application import TaskService
from developer_task_manager.persistence import JsonTaskRepository
from developer_task_manager.ui import TaskManagerApp


APPLICATION_DIR = Path(__file__).resolve().parent
DATA_FILE = APPLICATION_DIR / "data" / "tasks.json"
LEGACY_DATA_FILE = APPLICATION_DIR.parent / "tasks.json"


def select_data_file() -> Path:
    """Use packaged data, or the legacy root file until it has been migrated."""
    if DATA_FILE.exists() or not LEGACY_DATA_FILE.exists():
        return DATA_FILE
    return LEGACY_DATA_FILE


def main() -> None:
    root = tk.Tk()
    try:
        service = TaskService(JsonTaskRepository(select_data_file()))
    except Exception as exc:
        from tkinter import messagebox

        root.withdraw()
        messagebox.showerror("Could not load tasks", str(exc))
        root.destroy()
        return
    TaskManagerApp(root, service)
    root.mainloop()


if __name__ == "__main__":
    main()

