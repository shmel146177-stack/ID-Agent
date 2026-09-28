# Storage inventory

Run from the ID-Agent repository on Windows:

```powershell
.\.venv\Scripts\python.exe -B -m app.services.storage_inventory C:\Projects --depth 3 --top 30
```

The command reads filesystem metadata and prints apparent sizes and file counts.
It never deletes or moves files. `-B` also prevents Python bytecode cache writes.
Use `--json` for machine-readable output; the command still writes only to stdout.

Rows are nested and overlap: do not add them together. Apparent size may count
hard links more than once and does not predict how much disk space deletion would
free. Links and Windows reparse points are never followed. Read errors and
skipped links make `Complete: no`; their paths are listed in the output or JSON.

Categories describe the role suggested by the path, not proof that anything
can be deleted. `inspect manually` includes temporary, audit, and validation
directories, which can still contain unique work. `project data`, source
documents, issued versions, reference templates, Git history, and the active
environment are protected categories. Review source ownership and copies
separately before any cleanup.
