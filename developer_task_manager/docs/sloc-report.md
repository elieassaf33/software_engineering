# Source lines of code report

## Result

Generated on 2026-08-04:

| Category | Python files | SLOC |
|---|---:|---:|
| Production | 12 | 814 |
| Tests | 5 | 226 |
| Total | 17 | 1,040 |

The legacy root `task_manager.py` is preserved for historical comparison and is
not included because it is not part of the refactored application's package.
Documentation and Mermaid sources are also excluded.

## Reproducible method

This is physical Python SLOC: every non-empty line whose first non-whitespace
character is not `#`. Docstring lines are included because they are executable
Python string expressions. Production includes every `.py` file below
`developer_task_manager` except `tests`; test code includes `.py` files under
`developer_task_manager/tests`.

The PowerShell command used was:

```powershell
$prod = Get-ChildItem developer_task_manager -Recurse -Filter *.py |
  Where-Object { $_.FullName -notmatch '[\\/]tests[\\/]' }
$tests = Get-ChildItem developer_task_manager\tests -Recurse -Filter *.py
function Measure-Sloc($files) {
  ($files | Get-Content |
    Where-Object { $_.Trim() -ne '' -and
      -not $_.TrimStart().StartsWith('#') }).Count
}
"production_files=$($prod.Count) production_sloc=$(Measure-Sloc $prod)"
"test_files=$($tests.Count) test_sloc=$(Measure-Sloc $tests)"
```

