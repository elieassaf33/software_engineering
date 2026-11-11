# Developer Context Task Manager

A local, single-user Python/Tkinter application created for IU module DLBCSPSE01.
It manages development tasks and records a structured **Developer Context
Snapshot**, so an interrupted developer can quickly recover the project, tool,
branch, files, command, current problem, and next action.

## Features

- Create, list, inspect, edit, and delete tasks.
- Stable UUID task IDs and UTC creation/modification timestamps.
- Status workflow: Planned, In Progress, Paused, and Completed.
- Reopen a completed task as In Progress.
- Search title, notes, and all context fields.
- Filter by status and normalized tag.
- A focused Resume Context view.
- Automatic UTF-8 JSON persistence after every successful change.
- Safe handling of missing, empty, malformed, and structurally invalid data.
- Import of the original `name`/`tool`/`notes`/`tags`/`completed` JSON schema.

## Architecture

The code uses four layers under `developer_task_manager/`:

- `domain`: `Task`, `ContextSnapshot`, validation, tags, and status rules.
- `application`: `TaskService` use cases, lookup, search, filtering, and rollback.
- `persistence`: repository abstraction and atomic JSON implementation.
- `ui`: Tkinter widgets and user interaction.

`main.py` constructs a concrete JSON repository and injects it into the service.
The application layer therefore has no dependency on a particular storage
implementation. See [architecture.md](developer_task_manager/docs/architecture.md).

## Requirements and installation

- Python 3.10 or newer.
- Tkinter (normally bundled with Windows and macOS Python; some Linux
  distributions package it separately as `python3-tk`).
- `pytest` is needed only for tests.

From the repository root:

```powershell
python -m pip install -r developer_task_manager/requirements.txt
```

No third-party runtime package is required.

## Launch

From the repository root:

```powershell
python -m developer_task_manager.main
```

The path is resolved from the installed application code, not the terminal's
working directory.

## Tests

```powershell
python -m pytest developer_task_manager/tests -q
```

Tests use pytest temporary directories and do not access the real application
data. The latest verified result is recorded in
[test-report.md](developer_task_manager/docs/test-report.md).

## JSON storage

New installations store tasks in
`developer_task_manager/data/tasks.json`. If the repository-root legacy
`tasks.json` already exists and the new data file does not, the application
loads and continues using that legacy location to avoid silently abandoning
existing data. Legacy entries are converted in memory and receive UUIDs and UTC
timestamps; the next successful save writes the new schema.

Writes use a temporary file in the same directory, flush it, and atomically
replace the target. A corrupt source file is reported and left unchanged.

## Documentation

- [Requirements](developer_task_manager/docs/requirements.md)
- [Architecture and trade-offs](developer_task_manager/docs/architecture.md)
- [Test report](developer_task_manager/docs/test-report.md)
- [SLOC report](developer_task_manager/docs/sloc-report.md)
- [Editable UML sources](developer_task_manager/docs/uml/README.md)

## Known limitations

- It is a local, single-user prototype with no authentication, synchronization,
  encryption, conflict resolution, or multi-process locking.
- JSON is appropriate for the current data volume but offers no query engine or
  transaction support beyond atomic whole-file replacement.
- Legacy tasks have no historical IDs or timestamps, so these are generated
  when loaded.
- File paths and commands are recorded as text; the application does not open
  files or execute commands.
- Tkinter UI behavior is exercised manually; automated tests cover domain,
  application, and persistence logic rather than widget rendering.

