from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from developer_task_manager.application import TaskNotFoundError, TaskService
from developer_task_manager.domain import ContextSnapshot, Task, TaskStatus, ValidationError
from developer_task_manager.persistence import RepositoryError


class TaskManagerApp:
    """Tkinter presentation for task and context-restoration workflows."""

    def __init__(self, root: tk.Tk, service: TaskService) -> None:
        self.root = root
        self.service = service
        self.visible_task_ids: list[str] = []
        self.selected_task_id: str | None = None
        self.root.title("Developer Context Task Manager")
        self.root.minsize(1050, 690)
        self._build_ui()
        self.refresh_tasks()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(1, weight=1)

        filters = ttk.LabelFrame(outer, text="Search and filter", padding=8)
        filters.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        filters.columnconfigure(1, weight=1)
        ttk.Label(filters, text="Search").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        search = ttk.Entry(filters, textvariable=self.search_var)
        search.grid(row=0, column=1, sticky="ew", padx=5)
        search.bind("<KeyRelease>", lambda _event: self.refresh_tasks())
        ttk.Label(filters, text="Status").grid(row=0, column=2, padx=(8, 0))
        self.status_filter = tk.StringVar(value="All")
        status_filter = ttk.Combobox(
            filters,
            textvariable=self.status_filter,
            values=["All", *(status.value for status in TaskStatus)],
            state="readonly",
            width=13,
        )
        status_filter.grid(row=0, column=3, padx=5)
        status_filter.bind("<<ComboboxSelected>>", lambda _event: self.refresh_tasks())
        ttk.Label(filters, text="Tag").grid(row=0, column=4)
        self.tag_filter = tk.StringVar(value="All")
        self.tag_combo = ttk.Combobox(
            filters, textvariable=self.tag_filter, values=["All"], state="readonly", width=14
        )
        self.tag_combo.grid(row=0, column=5, padx=5)
        self.tag_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_tasks())
        ttk.Button(filters, text="Clear", command=self.clear_filters).grid(row=0, column=6)

        list_frame = ttk.LabelFrame(outer, text="Tasks", padding=8)
        list_frame.grid(row=1, column=0, sticky="nsw", padx=(0, 8))
        list_frame.rowconfigure(0, weight=1)
        self.task_list = tk.Listbox(list_frame, width=38, height=28, exportselection=False)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_list.yview)
        self.task_list.configure(yscrollcommand=scrollbar.set)
        self.task_list.grid(row=0, column=0, sticky="ns")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.task_list.bind("<<ListboxSelect>>", self._select_task)

        actions = ttk.Frame(list_frame)
        actions.grid(row=1, column=0, columnspan=2, pady=(8, 0))
        ttk.Button(actions, text="New", command=self.clear_form).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions, text="Delete", command=self.delete_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions, text="Resume Context", command=self.show_resume_context).pack(
            side=tk.LEFT, padx=2
        )

        notebook = ttk.Notebook(outer)
        notebook.grid(row=1, column=1, sticky="nsew")
        self.form_tab = ttk.Frame(notebook, padding=10)
        self.resume_tab = ttk.Frame(notebook, padding=10)
        notebook.add(self.form_tab, text="Task editor")
        notebook.add(self.resume_tab, text="Resume context")
        self.notebook = notebook
        self._build_form()
        self._build_resume_tab()

    def _build_form(self) -> None:
        self.form_tab.columnconfigure(1, weight=1)
        self.entries: dict[str, tk.StringVar] = {
            name: tk.StringVar()
            for name in (
                "title",
                "project_name",
                "tool",
                "git_branch",
                "file_paths",
                "last_command",
                "tags",
            )
        }
        rows = [
            ("Title *", "title"),
            ("Project", "project_name"),
            ("Tool / IDE", "tool"),
            ("Git branch", "git_branch"),
            ("File paths (comma-separated)", "file_paths"),
            ("Last command", "last_command"),
            ("Tags (comma-separated)", "tags"),
        ]
        for row, (label, key) in enumerate(rows):
            ttk.Label(self.form_tab, text=label).grid(row=row, column=0, sticky="nw", pady=3)
            ttk.Entry(self.form_tab, textvariable=self.entries[key]).grid(
                row=row, column=1, sticky="ew", padx=(8, 0), pady=3
            )

        text_start = len(rows)
        self.text_fields: dict[str, tk.Text] = {}
        for offset, (label, key) in enumerate(
            (
                ("Current problem / progress", "progress_note"),
                ("Next action", "next_action"),
                ("Notes", "notes"),
            )
        ):
            row = text_start + offset
            ttk.Label(self.form_tab, text=label).grid(row=row, column=0, sticky="nw", pady=3)
            text = tk.Text(self.form_tab, height=3, wrap=tk.WORD)
            text.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=3)
            self.text_fields[key] = text

        status_row = text_start + 3
        ttk.Label(self.form_tab, text="Status").grid(row=status_row, column=0, sticky="w")
        self.status_var = tk.StringVar(value=TaskStatus.PLANNED.value)
        self.status_combo = ttk.Combobox(
            self.form_tab,
            textvariable=self.status_var,
            values=[status.value for status in TaskStatus],
            state="readonly",
        )
        self.status_combo.grid(row=status_row, column=1, sticky="w", padx=(8, 0))
        self.status_combo.bind("<<ComboboxSelected>>", self.change_selected_status)

        button_row = status_row + 1
        ttk.Button(self.form_tab, text="Create task", command=self.create_task).grid(
            row=button_row, column=0, pady=10
        )
        ttk.Button(self.form_tab, text="Save edits", command=self.save_edits).grid(
            row=button_row, column=1, sticky="w", padx=8, pady=10
        )
        ttk.Label(
            self.form_tab,
            text="Changes are saved automatically when an operation succeeds.",
            foreground="#555555",
        ).grid(row=button_row + 1, column=0, columnspan=2, sticky="w")

    def _build_resume_tab(self) -> None:
        self.resume_tab.columnconfigure(0, weight=1)
        self.resume_tab.rowconfigure(1, weight=1)
        ttk.Label(
            self.resume_tab,
            text="Resume Context",
            font=("TkDefaultFont", 15, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.resume_text = tk.Text(self.resume_tab, wrap=tk.WORD, state=tk.DISABLED)
        self.resume_text.grid(row=1, column=0, sticky="nsew")
        ttk.Button(
            self.resume_tab, text="Reopen completed task", command=self.reopen_selected
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))

    def _context_from_form(self) -> ContextSnapshot:
        return ContextSnapshot(
            project_name=self.entries["project_name"].get(),
            tool=self.entries["tool"].get(),
            git_branch=self.entries["git_branch"].get(),
            file_paths=self.entries["file_paths"].get(),
            last_command=self.entries["last_command"].get(),
            progress_note=self._text("progress_note"),
            next_action=self._text("next_action"),
        )

    def _text(self, key: str) -> str:
        return self.text_fields[key].get("1.0", tk.END).strip()

    def _handle_error(self, action: str, exc: Exception) -> None:
        if isinstance(exc, (ValidationError, TaskNotFoundError, RepositoryError, ValueError)):
            messagebox.showerror(action, str(exc), parent=self.root)
        else:
            messagebox.showerror(action, f"Unexpected error: {exc}", parent=self.root)

    def create_task(self) -> None:
        try:
            task = self.service.create_task(
                title=self.entries["title"].get(),
                context=self._context_from_form(),
                notes=self._text("notes"),
                tags=self.entries["tags"].get(),
            )
        except Exception as exc:
            self._handle_error("Could not create task", exc)
            return
        self.selected_task_id = task.id
        self.refresh_tasks(select_id=task.id)

    def save_edits(self) -> None:
        if not self.selected_task_id:
            messagebox.showinfo("No task selected", "Select a task to edit.", parent=self.root)
            return
        try:
            task = self.service.edit_task(
                self.selected_task_id,
                title=self.entries["title"].get(),
                context=self._context_from_form(),
                notes=self._text("notes"),
                tags=self.entries["tags"].get(),
            )
        except Exception as exc:
            self._handle_error("Could not save task", exc)
            return
        self.refresh_tasks(select_id=task.id)

    def change_selected_status(self, _event: object = None) -> None:
        if not self.selected_task_id:
            self.status_var.set(TaskStatus.PLANNED.value)
            return
        try:
            task = self.service.change_status(self.selected_task_id, self.status_var.get())
        except Exception as exc:
            self._handle_error("Could not change status", exc)
            self._load_selected()
            return
        self.refresh_tasks(select_id=task.id)

    def reopen_selected(self) -> None:
        if not self.selected_task_id:
            messagebox.showinfo("No task selected", "Select a completed task.", parent=self.root)
            return
        try:
            task = self.service.reopen_task(self.selected_task_id)
        except Exception as exc:
            self._handle_error("Could not reopen task", exc)
            return
        self.refresh_tasks(select_id=task.id)
        self.show_resume_context()

    def delete_selected(self) -> None:
        if not self.selected_task_id:
            messagebox.showinfo("No task selected", "Select a task to delete.", parent=self.root)
            return
        if not messagebox.askyesno(
            "Delete task", "Permanently delete the selected task?", parent=self.root
        ):
            return
        try:
            self.service.delete_task(self.selected_task_id)
        except Exception as exc:
            self._handle_error("Could not delete task", exc)
            return
        self.clear_form()
        self.refresh_tasks()

    def refresh_tasks(self, select_id: str | None = None) -> None:
        status = self.status_filter.get()
        tag = self.tag_filter.get()
        try:
            tasks = self.service.list_tasks(
                query=self.search_var.get(),
                status=None if status == "All" else status,
                tag="" if tag == "All" else tag,
            )
        except Exception as exc:
            self._handle_error("Could not filter tasks", exc)
            return
        self.task_list.delete(0, tk.END)
        self.visible_task_ids = []
        for task in tasks:
            self.visible_task_ids.append(task.id)
            self.task_list.insert(
                tk.END, f"[{task.status.value}] {task.title} — {task.context.project_name}"
            )
        tags = ["All", *self.service.available_tags()]
        self.tag_combo.configure(values=tags)
        if self.tag_filter.get() not in tags:
            self.tag_filter.set("All")
        target = select_id or self.selected_task_id
        if target in self.visible_task_ids:
            index = self.visible_task_ids.index(target)
            self.task_list.selection_set(index)
            self.task_list.see(index)
            self.selected_task_id = target
            self._load_selected()
        elif target:
            self.selected_task_id = None

    def clear_filters(self) -> None:
        self.search_var.set("")
        self.status_filter.set("All")
        self.tag_filter.set("All")
        self.refresh_tasks()

    def clear_form(self) -> None:
        self.selected_task_id = None
        self.task_list.selection_clear(0, tk.END)
        for variable in self.entries.values():
            variable.set("")
        for text in self.text_fields.values():
            text.delete("1.0", tk.END)
        self.status_var.set(TaskStatus.PLANNED.value)
        self._set_resume_text("Select a task to view its resume context.")

    def _select_task(self, _event: object = None) -> None:
        selection = self.task_list.curselection()
        if not selection:
            return
        self.selected_task_id = self.visible_task_ids[selection[0]]
        self._load_selected()

    def _load_selected(self) -> None:
        if not self.selected_task_id:
            return
        try:
            task = self.service.get_task(self.selected_task_id)
        except TaskNotFoundError as exc:
            self._handle_error("Task unavailable", exc)
            return
        values = {
            "title": task.title,
            "project_name": task.context.project_name,
            "tool": task.context.tool,
            "git_branch": task.context.git_branch,
            "file_paths": ", ".join(task.context.file_paths),
            "last_command": task.context.last_command,
            "tags": ", ".join(task.tags),
        }
        for key, value in values.items():
            self.entries[key].set(value)
        for key, value in (
            ("progress_note", task.context.progress_note),
            ("next_action", task.context.next_action),
            ("notes", task.notes),
        ):
            self.text_fields[key].delete("1.0", tk.END)
            self.text_fields[key].insert("1.0", value)
        self.status_var.set(task.status.value)
        self._set_resume_text(self._format_resume(task))

    def show_resume_context(self) -> None:
        if not self.selected_task_id:
            messagebox.showinfo("No task selected", "Select a task to resume.", parent=self.root)
            return
        self._load_selected()
        self.notebook.select(self.resume_tab)

    def _set_resume_text(self, content: str) -> None:
        self.resume_text.configure(state=tk.NORMAL)
        self.resume_text.delete("1.0", tk.END)
        self.resume_text.insert("1.0", content)
        self.resume_text.configure(state=tk.DISABLED)

    @staticmethod
    def _format_resume(task: Task) -> str:
        context = task.context
        paths = "\n".join(f"  • {path}" for path in context.file_paths) or "  (none)"
        return (
            f"{task.title}\n"
            f"Status: {task.status.value}\n"
            f"Project: {context.project_name or '(not set)'}\n"
            f"Tool / IDE: {context.tool or '(not set)'}\n"
            f"Git branch: {context.git_branch or '(not set)'}\n\n"
            f"NEXT ACTION\n{context.next_action or '(not set)'}\n\n"
            f"CURRENT PROBLEM / PROGRESS\n{context.progress_note or '(not set)'}\n\n"
            f"LAST COMMAND\n{context.last_command or '(not set)'}\n\n"
            f"RELEVANT FILES\n{paths}\n\n"
            f"NOTES\n{task.notes or '(none)'}\n\n"
            f"Tags: {', '.join(task.tags) or '(none)'}\n"
            f"Task ID: {task.id}\n"
            f"Created: {task.created_at.isoformat()}\n"
            f"Modified: {task.modified_at.isoformat()}"
        )
