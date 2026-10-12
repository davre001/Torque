# Phase 1: cloud preparation

Implemented code is opt-in. Local SQLite and the separate local worker remain
available. No Render, Vercel or Neon service has been provisioned by this change.

## Database and migrations

Set `TORQUE_DATABASE_URL` to a PostgreSQL URL. Remote connections must specify
`sslmode=require`, `verify-ca` or `verify-full`. When empty, `TORQUE_DATABASE`
continues to select the local SQLite file. Keep connection strings out of chat,
source control and browser-visible environment variables.

Run `python -m backend migrate` after installing `requirements.txt`. Schema version
1 includes users, runs, jobs, attempts, events, publication leases, spending
reservations, OAuth states, encrypted GitHub connections, browser sessions,
HTTP counters, dispatch records and private artifact records. Initialization is
transactional and repeatable; newer schema versions are rejected. PostgreSQL
runtime initialization verifies the version without DDL; the `migrate` command
uses `TORQUE_MIGRATION_DATABASE_URL` when configured. This creates
an empty cloud schema; it does not import local history or credentials.

PostgreSQL uses a transaction-scoped advisory lock across all cooperating Torque
database transactions. This preserves the prototype's serialized admission and
single active worker behavior. Locks have a 10-second timeout; statements have a
20-second timeout. Keep network/provider calls outside these transactions.
It is a bounded deployment design, not a high-throughput queue.

## Worker dispatch

Set `TORQUE_WORKER_DISPATCH=github-actions` on the API only after the database and
agent workflow are provisioned. Submitting a job persists its reservation and
dispatch identity atomically. GitHub POST failures leave an uncertain dispatch;
no reservation is refunded or charged a second time. Retry/reconciliation uses
the same request ID. Duplicate workflow runs cannot claim an already running or
finished job.

`python -m backend worker --run-id <32-character-run-id>` claims only the assigned
job and exits after one run. Its exit does not indicate that a queued job was
claimed: global single-worker limits can defer execution. The outbox reconciler
handles queued work. Existing `worker` and `worker --once` retain local behavior.

New workflows:

- `torque-agent-worker.yml`: trusted credential-bearing agent execution.
- `torque-dispatch-reconcile.yml`: bounded manual reconciliation, no paid model call.
- `torque-storage-checks.yml`: disposable PostgreSQL integration tests, no application credentials.

Create a protected `torque-production` Actions environment, restrict deployment
branches to the reviewed default branch, and provision its secrets/variables
before activation. Do not run target repository scripts in the agent job. The
existing acceptance workflow remains separate and credential-free.

Run `python -m backend dispatch` or the reconciliation workflow after failed
dispatches. Automatic scheduling is deliberately not enabled before provisioning;
enable a bounded schedule during deployment so queued work does not depend on
Render being awake. GitHub concurrency may replace pending workflows; database
leases and reconciliation remain authoritative. Expired executions become
interrupted and are never automatically replayed.

## Durable artifacts and publication

For the bounded hackathon deployment, PostgreSQL also stores private JSON
artifacts, capped at 2 MiB per record and 8 MiB per run. This replaces the earlier proposed separate
object-storage account. Local worker files are caches only. Each record is
immutable by run/name and verified against the hash in the persisted run manifest.

A verified run saves the complete reviewed context before readiness. Cloud
publication retrieves artifacts and verified contents from the database, checks
all acceptance criteria and hashes, and retains existing destination authorization
and publication leases. It does not require the expired runner's workspace.

`python -m backend cleanup --keep-days 7` previews retention; add `--apply` to
delete eligible artifacts. Ready/publishing runs and active publication owners
are excluded. Database history remains. Monitor total database storage: per-record
caps do not guarantee that a free database will never fill up. Back up the database
and preserve the encryption key securely before migration or retention.

## Same-origin frontend proxy

Production browser calls default to relative `/api/...` URLs. The new Next.js route
forwards only authentication and run routes to `TORQUE_BACKEND_ORIGIN`. Configure
that HTTPS origin, `TORQUE_FRONTEND_ORIGIN` and the same random
`TORQUE_PROXY_SECRET` on the frontend server and API. These are server variables;
the secret must never have a `NEXT_PUBLIC_` prefix.

Set the GitHub callback to the frontend production origin plus
`/api/auth/github/callback`. The proxy preserves separate Set-Cookie headers and
manual OAuth redirects, forwards cookies/CSRF/idempotency headers, rejects
cross-origin POSTs, bounds streamed bodies at 64 KiB and times out upstream calls
after 50 seconds. Backend public mode accepts its configured Render hostname
and requires the proxy secret except for `/health`.

Do not enable Uvicorn's blanket trust of forwarded client addresses. Current
backend rate limits may group all proxy requests under one upstream IP until
trusted production client-IP handling is verified. Publication can outlast a
proxy timeout; check status and retry the same destination to reconcile, never
assume a timeout means GitHub writes did not happen.

## Validation

`python -m backend preflight --cloud-probe` checks configured database tables and
read-only access to the active agent workflow. It emits statuses, not credentials.
Its cloud result does not establish provider availability, browser login or
successful execution/publication. Ordinary preflight adds configuration-only
cloud status. Run staging checks before public release.

Local commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
node tests/proxy-contract.cjs
```

Actual PostgreSQL tests require `TORQUE_TEST_DATABASE_URL`. They create and remove
unique `torque_test_*` schemas in a dedicated test database; do not use production.
The storage-check workflow supplies its own disposable PostgreSQL service.
Two PostgreSQL integration tests passed against the newly configured empty Neon
database in isolated temporary schemas, which were removed afterward. They cover
migrations, concurrency, cancellation/expiry, artifacts, counters and publication
fencing. Production-browser OAuth and the deployed end-to-end workflow remain
pending. See [deployment checklist](../deployment.md).

Local validation for this change: 166 Python tests passed, three skipped (including
the two PostgreSQL integration tests without a test database). The proxy contract
checks and production Next.js build passed. No paid model trial, cloud deployment,
workflow dispatch was performed in that local validation pass. Subsequently, the
Neon schema was initialized and the two isolated database tests passed; see
`evidence/deployment/neon-storage-checks.json`. Existing SQLite history has not
been imported into Neon.

Phase 3 verification additionally passed against a disposable Neon schema:
immutable/idempotent artifact writes, secret redaction, record/run limits,
tamper detection, verified publication retrieval after local-file removal and
retention preserving publishable runs. The runtime artifact table has no PUBLIC
grants and the runtime role cannot create schema objects. See
`evidence/deployment/private-artifact-checks.json` for representative sizes.
The account's remaining storage allowance, off-machine backup custody and
deployed log/end-to-end checks remain release gates. Local credential auditing
now includes durable artifact contents; it does not inspect deployed logs.
