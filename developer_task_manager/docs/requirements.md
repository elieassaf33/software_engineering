# Requirements

## Functional requirements

- **FR-01:** The system shall create a task with a non-empty title and structured
  Developer Context Snapshot.
- **FR-02:** The system shall assign each new task a stable, unique ID.
- **FR-03:** The system shall list all stored tasks at startup.
- **FR-04:** The system shall display every stored field of a selected task.
- **FR-05:** The system shall edit a task without changing its ID or creation
  timestamp.
- **FR-06:** The system shall permit only the transitions Planned→In Progress,
  Planned→Completed, In Progress→Paused, In Progress→Completed,
  Paused→In Progress, Paused→Completed, and Completed→In Progress.
- **FR-07:** The system shall reopen a Completed task as In Progress.
- **FR-08:** The system shall delete a selected task only after UI confirmation.
- **FR-09:** Search shall match case-insensitive text in title, notes, project,
  tool, branch, file paths, last command, progress, or next action.
- **FR-10:** The system shall filter tasks by one status and/or one normalized tag.
- **FR-11:** Each successful create, edit, status, reopen, or delete operation
  shall save the complete task collection automatically.
- **FR-12:** The Resume Context view shall prioritize next action, progress,
  command, files, project, tool, and branch.
- **FR-13:** The JSON repository shall load the legacy task schema when all
  legacy field types are valid.

## Nonfunctional requirements

- **NFR-01:** Runtime code shall use Python 3.10+ and the standard-library
  Tkinter UI; no web or cloud service is required.
- **NFR-02:** Domain construction shall reject an empty title.
- **NFR-03:** Tags shall be trimmed, lowercased, empty values removed, and
  duplicates removed while retaining first-seen order.
- **NFR-04:** JSON shall be read and written explicitly as UTF-8.
- **NFR-05:** A missing or whitespace-only data file shall load as an empty task
  collection.
- **NFR-06:** Malformed or structurally invalid JSON shall produce a
  `RepositoryError` and shall not modify the source file.
- **NFR-07:** Saving shall write a temporary sibling file, flush it, and replace
  the destination atomically.
- **NFR-08:** The application data path shall be derived from the application
  directory, independent of the current working directory.
- **NFR-09:** Unknown task IDs and storage errors shall be converted to handled,
  understandable errors at the UI boundary.
- **NFR-10:** Persistence tests shall use temporary directories and not modify
  application data.
- **NFR-11:** Creation and modification timestamps shall be timezone-aware ISO
  8601 values and survive a save/load round trip.
- **NFR-12:** Business services shall depend on `TaskRepository`, not directly
  on `JsonTaskRepository`.

