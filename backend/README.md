# Running the backend

Implemented: SQLite history/queue, separate worker, cancellation/leases, pinned source
snapshots, bounded file edits, Claude/LiteLLM and Gemini adapters, agent roles, verification
gates, bounded recovery, atomic artifacts, and worker-owned Neatlogs tracing.
The demo pipeline has passed live provider calls and independent remote browser tests.
Explicit controlled-fork draft PR publication is implemented and tested with mocked GitHub
responses; live publication and finalized dashboard traces remain unverified.
GitHub visitor login is still pending.

Install from the repository root:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
```

For the exact environment used by the tests, install `requirements.lock.txt` instead.
The lock records the existing project virtual environment, including neatlogs dependencies.

Set these in the existing root `.env`:

- `TORQUE_OPERATOR_TOKEN`: a new random local access token, separate from GitHub/provider keys.
- `TORQUE_ALLOWED_REPOSITORIES=GabrieleLozupone/kokon`: explicit read-only demo scope.
- Existing `GITHUB_TOKEN` authenticates source reads and explicit publication; public issue reads also work without it.
- `TORQUE_RECIPES_FILE`: operator-reviewed mapping based on `backend/recipes.example.json`.
- Explicit conservative cost rates for both models, using the four new variables in `.env.example`.
  Use zero only for verified free quota; blank rates fail preflight.
- Existing provider models, keys, gateway URL, and Neatlogs project key.

Recipes restrict context/editable paths and define immutable acceptance criteria.
Each recipe needs an installed immutable Docker image and an independent test suite.
See [kokon acceptance setup](../tests/acceptance/kokon/README.md). The example contains
deliberately invalid placeholders: replace them with real image/suite values.
Docker is currently unavailable in this workspace, so the worker fails before model spend.

Alternatively, set `TORQUE_RUNNER=github-actions` and follow
[remote Linux runner setup](REMOTE_RUNNER.md). That path needs no local Docker or rented
server. The remote workflow must be pushed and an Actions-scoped token configured first;
it has not yet passed a live acceptance run.

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
The worker performs investigation with Gemini, implementation with Claude via LiteLLM,
independent Docker tests, Gemini review, and up to two Claude recovery diagnoses.
A passing run stops at `ready_to_publish`. See [PR publication](PUBLICATION.md) for explicit publication to a controlled destination.
Failed tests cannot be overridden by model approval. Infrastructure failures cannot
count as bug reproduction. Recovery is labeled `local-artifacts` until hosted readback exists.

Model SDK retries are disabled; explicit transport retries have separate counters and
reserve budget even when a request's billing outcome is uncertain. Reported tokens
are stored; costs are estimates using configured conservative rates, not billing receipts.
Missing usage stops a run. Prompt/source content is omitted from exported telemetry.
Check `preflight` before launching a worker; readiness reports configuration presence
and never claims live integrations passed. The existing local `.env` is unchanged.
