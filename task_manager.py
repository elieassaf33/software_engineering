import tkinter as tk
from tkinter import messagebox
import json
import os

TASKS_FILE = "tasks.json"


# -----------------------------
# Task Object
# -----------------------------
class Task:
    def __init__(self, name, tool, notes, tags, completed=False):
        self.name = name
        self.tool = tool
        self.notes = notes
        self.tags = tags
        self.completed = completed

    def to_dict(self):
        return {
            "name": self.name,
            "tool": self.tool,
            "notes": self.notes,
            "tags": self.tags,
            "completed": self.completed
        }


# -----------------------------
# Persistence Layer
# -----------------------------
def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []

    with open(TASKS_FILE, "r") as f:
        data = json.load(f)

    return [Task(**task) for task in data]


def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump([task.to_dict() for task in tasks], f, indent=4)


# -----------------------------
# Task Management Subsystem
# -----------------------------
class TaskManager:
    def __init__(self):
        self.tasks = load_tasks()

    def get_tasks(self):
        return self.tasks

    def add_task(self, name, tool, notes, tags):
        new_task = Task(name, tool, notes, tags)
        self.tasks.append(new_task)
        save_tasks(self.tasks)

    def complete_task(self, index):
        self.tasks[index].completed = True
        save_tasks(self.tasks)

    def delete_task(self, index):
        del self.tasks[index]
        save_tasks(self.tasks)


# -----------------------------
# UI Subsystem
# -----------------------------
class TaskManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Developer Task Manager")

        # Use the TaskManager subsystem
        self.manager = TaskManager()

        # Main frame
        self.frame = tk.Frame(root)
        self.frame.pack(padx=10, pady=10)

        # Task list
        self.task_listbox = tk.Listbox(self.frame, width=50, height=10)
        self.task_listbox.grid(row=0, column=0, columnspan=3, pady=5)
        self.task_listbox.bind("<<ListboxSelect>>", self.show_task_details)

        self.refresh_task_list()

        # Task fields
        tk.Label(self.frame, text="Task Name:").grid(row=1, column=0, sticky="w")

        self.entry_name = tk.Entry(self.frame, width=40)
        self.entry_name.grid(row=1, column=1, columnspan=2)

        tk.Label(self.frame, text="Tool Used:").grid(row=2, column=0, sticky="w")

        self.entry_tool = tk.Entry(self.frame, width=40)
        self.entry_tool.grid(row=2, column=1, columnspan=2)

        tk.Label(self.frame, text="Context Notes:").grid(row=3, column=0, sticky="w")

        self.entry_notes = tk.Entry(self.frame, width=40)
        self.entry_notes.grid(row=3, column=1, columnspan=2)

        tk.Label(self.frame, text="Tags:").grid(row=4, column=0, sticky="w")

        self.entry_tags = tk.Entry(self.frame, width=40)
        self.entry_tags.grid(row=4, column=1, columnspan=2)

        # Buttons
        tk.Button(
            self.frame,
            text="Add Task",
            command=self.add_task
        ).grid(row=5, column=0, pady=5)

        tk.Button(
            self.frame,
            text="Mark Completed",
            command=self.complete_task
        ).grid(row=5, column=1, pady=5)

        tk.Button(
            self.frame,
            text="Delete Task",
            command=self.delete_task
        ).grid(row=5, column=2, pady=5)

        # Task details
        tk.Label(
            self.frame,
            text="Task Details:"
        ).grid(row=6, column=0, sticky="w", pady=(10, 0))

        self.details_box = tk.Text(
            self.frame,
            width=50,
            height=6,
            state="disabled"
        )

        self.details_box.grid(row=7, column=0, columnspan=3, pady=5)

    def refresh_task_list(self):
        self.task_listbox.delete(0, tk.END)

        for task in self.manager.get_tasks():
            status = "✔" if task.completed else "✖"
            self.task_listbox.insert(
                tk.END,
                f"{status} {task.name}"
            )

    def add_task(self):
        name = self.entry_name.get().strip()
        tool = self.entry_tool.get().strip()
        notes = self.entry_notes.get().strip()
        tags = self.entry_tags.get().strip()

        if not name:
            messagebox.showwarning(
                "Missing Data",
                "Task name is required."
            )
            return

        self.manager.add_task(name, tool, notes, tags)

        self.refresh_task_list()

        self.entry_name.delete(0, tk.END)
        self.entry_tool.delete(0, tk.END)
        self.entry_notes.delete(0, tk.END)
        self.entry_tags.delete(0, tk.END)

    def complete_task(self):
        selection = self.task_listbox.curselection()

        if not selection:
            messagebox.showwarning(
                "No Selection",
                "Select a task to complete."
            )
            return

        index = selection[0]

        self.manager.complete_task(index)

        self.refresh_task_list()
        self.show_task_details()

    def delete_task(self):
        selection = self.task_listbox.curselection()

        if not selection:
            messagebox.showwarning(
                "No Selection",
                "Select a task to delete."
            )
            return

        index = selection[0]

        confirm = messagebox.askyesno(
            "Delete Task",
            "Are you sure you want to delete this task?"
        )

        if not confirm:
            return

        self.manager.delete_task(index)

        self.refresh_task_list()

        self.details_box.config(state="normal")
        self.details_box.delete("1.0", tk.END)
        self.details_box.config(state="disabled")

    def show_task_details(self, event=None):
        selection = self.task_listbox.curselection()

        if not selection:
            return

        index = selection[0]

        task = self.manager.get_tasks()[index]

        details = (
            f"Name: {task.name}\n"
            f"Tool Used: {task.tool}\n"
            f"Context Notes: {task.notes}\n"
            f"Tags: {task.tags}\n"
            f"Completed: {'Yes' if task.completed else 'No'}"
        )

        self.details_box.config(state="normal")
        self.details_box.delete("1.0", tk.END)
        self.details_box.insert(tk.END, details)
        self.details_box.config(state="disabled")


# -----------------------------
# Application Entry Point
# -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManagerApp(root)
    root.mainloop()