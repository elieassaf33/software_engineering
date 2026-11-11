# Test report

## Executed result

- Date: 2026-08-04
- Environment: Python 3.14.3 on Windows
- Command: `python -m pytest developer_task_manager/tests -q`
- Actual result: **24 passed in 0.11 seconds**
- Compilation check: `python -m compileall -q developer_task_manager`
  completed with exit code 0.

No performance, load, accessibility, or automated Tkinter widget tests were
executed.

## Requirement traceability

| Test or test group | Requirements covered |
|---|---|
| `test_valid_task_creation` | FR-01, FR-02, NFR-11 |
| `test_empty_title_is_rejected` | NFR-02 |
| `test_tags_are_trimmed_lowercase_deduplicated` | NFR-03 |
| `test_valid_status_transitions`, `test_invalid_status_transition_is_rejected` | FR-06 |
| `test_edit_preserves_id_and_creation_time`, `test_create_edit_and_delete` | FR-05, FR-08, FR-11 |
| `test_new_tasks_receive_unique_ids` | FR-02 |
| `test_searches_title_notes_and_context` | FR-09 |
| `test_filters_by_status_and_tag` | FR-10 |
| `test_reopens_completed_task` | FR-07 |
| `test_repository_save_error_rolls_back_create` | FR-11, NFR-09, NFR-12 |
| `test_invalid_id_operations_are_handled` | NFR-09 |
| `test_save_and_load_round_trip_preserves_fields_and_timestamps` | FR-03, NFR-04, NFR-07, NFR-11 |
| `test_missing_json_file_returns_empty_list`, `test_empty_json_file_returns_empty_list` | NFR-05 |
| `test_malformed_json_reports_error_without_modifying_file` | NFR-06 |
| `test_structurally_invalid_data_is_rejected`, `test_duplicate_ids_are_rejected` | NFR-06 |
| `test_legacy_format_is_loaded` | FR-13 |
| `test_save_wraps_file_system_errors` | NFR-09 |

FR-04, FR-12, NFR-01, and NFR-08 are verified by code inspection and manual
launch checks rather than automated widget tests. UI confirmation in FR-08 is
implemented in `TaskManagerApp.delete_selected`; service deletion is automated.
