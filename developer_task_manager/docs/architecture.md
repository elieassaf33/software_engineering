# Architecture

## Decision

A layered architecture separates volatile UI and storage details from the task
rules. The domain layer validates tasks and owns status transitions. The
application layer coordinates use cases. Persistence implements a small
`TaskRepository` abstraction. Tkinter presents the use cases. `main.py` is the
composition root that injects `JsonTaskRepository` into `TaskService`.

This structure is deliberately modest: it enables unit testing and future
storage replacement without introducing a framework or network service.

## Why JSON

JSON is readable, portable, in Python's standard library, and sufficient for a
small personal prototype. One file is easy to inspect and back up. The
repository explicitly uses UTF-8 and an atomic temporary-file replacement.
Malformed or structurally invalid content raises a readable `RepositoryError`;
it is never replaced during load.

## JSON versus SQLite

JSON has almost no setup and makes the submission easy to examine. Its costs are
whole-file reads/writes, limited concurrent access, no schema constraints, and
application-side search. SQLite would provide transactions, indexes, query
support, and better scaling, but would add schema/migration work that is not
justified by the prototype's current single-user scope. `TaskRepository` allows
an SQLite implementation later without changing `TaskService`.

## Tkinter versus alternatives

Tkinter is included with common Python distributions and keeps local execution
simple. It is adequate for forms, lists, filters, and the Resume Context view.
Qt provides richer widgets but adds a large dependency; a web UI would require
a server/browser architecture and expand the security and deployment scope.
Those alternatives do not fit this small desktop prototype.

## Reliability and dependencies

Domain validation remains active even when tasks are created outside the UI.
Status changes use an allow-list. Service operations save immediately and roll
back their in-memory mutation if saving fails. IDs, rather than list indices,
identify tasks. The JSON repository rejects duplicate IDs and invalid records.
The data path is based on `main.py`'s location.

Dependencies point inward conceptually: UI calls application use cases;
application uses domain entities and the repository abstraction; persistence
constructs domain entities. The composition root is the only place selecting
the JSON implementation.

## Privacy and local storage

Context may contain commands, paths, branch names, or notes that reveal
sensitive project information. Storage is local but not encrypted, and any
account or process with file access may read it. Users should apply operating
system permissions, avoid recording secrets, and protect backups. “Local” does
not imply confidential.

