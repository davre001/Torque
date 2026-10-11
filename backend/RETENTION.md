# Runtime file retention

The local operator can preview cleanup from the repository root:

```powershell
.\.venv\Scripts\python.exe -m backend cleanup
.\.venv\Scripts\python.exe -m backend cleanup --keep-days 14
```

Nothing is deleted without `--apply`. The default keeps seven days; the minimum is
one day. After reviewing the preview, the operator can apply the same policy:

```powershell
.\.venv\Scripts\python.exe -m backend cleanup --keep-days 14 --apply
```

Only `var/workspaces/<run-id>` and `var/artifacts/<run-id>` for old completed,
failed, cancelled, or interrupted runs with finished queue jobs are eligible.
Ready-to-publish patches, active/queued jobs, pending publication owners, unknown
directories, SQLite history/events, and committed `evidence/` are preserved.
The age comes from the saved run's last update, not file modification times.

Cleanup rejects paths outside the workspace and symlink/reparse paths, including
links inside a run directory. It rechecks eligibility under a short SQLite
transaction, renames eligible directories into `var/retention-trash`, and records
`result.retention.local_files_expired`. Recursive deletion happens after releasing
the transaction. This is an explicit CLI maintenance operation, not an automatic
background task or a browser endpoint.

If deletion fails after quarantine, the report lists the run as blocked and the
quarantined files remain for inspection. A crash between directory renames and
database commit may also leave quarantine files; automatic quarantine recovery is
not implemented. Do not blindly delete unknown files. Completed run history and PR
links remain available; local files are unavailable once the policy expires them.

The live preview currently selects no runs at the default seven-day cutoff.
Deletion and preservation behavior are tested with disposable fixtures; no existing
demo workspaces or artifacts were removed during setup.
