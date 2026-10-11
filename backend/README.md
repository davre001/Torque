# Running the backend

The first implemented milestone provides SQLite run/history storage, durable queueing,
a separate worker, cancellation, lease renewal, and read-only GitHub issue investigation.
Agent edits, isolated tests, verified publication, and GitHub visitor login are still pending.
The worker records that limitation as a failed outcome after fetching an issue.

Install from the repository root:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
```

For the exact environment used by the tests, install `requirements.lock.txt` instead.
The lock records the existing project virtual environment, including neatlogs dependencies.

Set these in the existing root `.env`:

- `TORQUE_OPERATOR_TOKEN`: a new random local access token, separate from GitHub/provider keys.
- `TORQUE_ALLOWED_REPOSITORIES=GabrieleLozupone/kokon`: explicit read-only demo scope.
- Existing `GITHUB_TOKEN` is used only by the worker; public issue reads also work without it.

Run the API and worker in separate terminals:

```powershell
.venv/Scripts/python.exe -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
.venv/Scripts/python.exe -m backend worker
```

The API has interactive documentation at http://127.0.0.1:8000/docs.
Requests to `/api/runs` require `Authorization: Bearer <TORQUE_OPERATOR_TOKEN>`.
No token is exposed by health responses. Keep the API bound to localhost.
The operator token is a development mechanism; it does not authenticate GitHub visitors.

```powershell
.venv/Scripts/python.exe -m backend preflight
.venv/Scripts/python.exe -m backend run https://github.com/GabrieleLozupone/kokon/issues/4
.venv/Scripts/python.exe -m backend status <run-id>
.venv/Scripts/python.exe -m pytest -q
```

`run` only enqueues; it requires a worker to process the job.
`worker --once` processes at most one queued job.
SQLite lives in ignored `var/torque.sqlite3`. Expired jobs become interrupted and
are never automatically replayed. History and events survive API restarts.
Events currently return paginated JSON, not SSE; Next.js is not yet connected.
No model calls, repository execution, pushes, or pull requests occur in this milestone.
