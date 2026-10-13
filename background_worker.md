# Torque background worker plan

## Database verification update — October 13, 2026

User-provided Neon SQL results confirm schema version 2 and runtime role
`torque_runtime_4833357e53e3` with all four elevated role flags disabled,
SELECT/INSERT/UPDATE/DELETE on all 15 Torque tables (including repository_setups),
no CREATE on public schema, and USAGE on the events sequence. These are user-reported
checks, not an independent agent query. Fresh schema-2 encrypted backup and
production worker/end-to-end verification remain pending.


## Current worker status — October 12, 2026

Connected-account update: the worker workflow was fetched from GitHub `main` and
its configuration matches this plan. All 47 repository Actions runs were checked;
none executed `torque-agent-worker.yml`. Hosted worker activation therefore
remains pending. GitHub repository/Actions reads work, but secret administration
and workflow dispatch are not available through this connection. Neon tools are
not yet exposed despite the user's reported connection.

The local separate worker and its recorded lifecycle checks are implemented.
Cloud mode adds shared PostgreSQL leases, private durable database artifacts,
`worker --run-id`, stable dispatch IDs and bounded reconciliation. The existing
`torque-agent-worker.yml` checks out without persisted credentials, runs Python
3.11, uses the protected `torque-production` environment, read-only contents
permission, concurrency one and a 25-minute timeout. The dispatch reconciler
exists but has no automatic schedule yet.

Current local checks: **192 Python tests passed, 5 skipped**, TypeScript, proxy
contracts and production frontend build passed. Dotenv was disabled for Python
tests; no `.env` or production credential-bearing worker was accessed. Older
SQLite-only descriptions below describe the local prototype and historical trials.

Still required: connected GitHub/Neon account access; provision/verify protected
worker secrets and variables; confirm schema **2** and `repository_setups` grants;
dispatch a real assigned job; prove artifacts survive runner deletion/API restart;
test cancellation, expiry, reconciliation and explicit idempotent publication;
enable bounded reconciliation scheduling after usage review. Paid-provider graceful
shutdown and successful unseeded recovery remain unverified. Hosted Entire context
remains disabled until runtime authentication is established.

The frontend is deployed at https://torque-pied.vercel.app, but a Vercel READY
deployment does not establish worker readiness. Render API
https://torque-sxqr.onrender.com passed health and basic proxied authentication
entry checks, but no hosted worker trial was performed. See [deployment status](deployment.md)
and [current verification](evidence/deployment/current-verification.json).

The `/workspace` submits and polls persisted runs. Local mode requires a separate
worker process. Cloud mode dispatches a targeted Actions worker through the API;
that path must be provisioned and verified before accepting production runs.

Frontend progress now reads persisted run events, including recovery and terminal
outcomes. History status refreshes during polling; completed results expose actual
acceptance/review records and PR links. Fixture browser tests cover the contract;
live connected-user execution/publication and user-confirmed browser history/disconnect are saved in `evidence/github-app/`.

Status: implemented separate SQLite-backed worker; live remote browser execution verified. [Backend overview](backend_implementation.md) defines the API and agent behavior; [integrations](integration.md) defines external access.

## Worker progress checklist

Current validation: 192 automated tests passed, five skipped (October 12, 2026). Windows signal
delivery during blocked localhost HTTP I/O is verified without transport retry;
the Linux workflow passed (Actions `38225586443`). This does not establish remote provider cancellation
or actual paid-provider graceful shutdown. Successful live recovery remains pending.

The worker is a separate process. FastAPI only submits jobs and reads state; it must not execute agents through `BackgroundTasks`.

Remote execution option: `TORQUE_RUNNER=github-actions` dispatches the reviewed kokon
acceptance workflow to GitHub-hosted Ubuntu. The local worker still owns jobs, model calls,
leases, and budgets; remote jobs only execute tests. See [setup](backend/REMOTE_RUNNER.md).
Live dispatch and all three browser criteria passed in the saved demo.

- [x] Select SQLite and one separate worker with concurrency one for the prototype.
- [x] Implement `backend/worker.py` and `backend/store.py`.
- [x] Implement queue schema, atomic job claims, ownership tokens, and persisted worker state.
- [x] Implement ` .\.venv\Scripts\python.exe -m backend worker`; CLI submissions enqueue for that worker.
- [x] Implement heartbeats during slow operations and reject expired-owner writes.
- [x] Enforce prototype concurrency one across competing worker processes.
- [x] Persist local attempt/test/recovery artifacts atomically before advancing pipeline state.
- [x] Separate bounded transport retries from the maximum two agent recovery retries.
- [x] Persist attempt outcomes and atomic artifact records before advancing stages.
- [x] Detect expired jobs on claim/startup and mark interrupted without replay.
- [x] Bound provider transport, one strict format-repair request, completed-result download retry, and agent recovery independently within shared limits; expired jobs are interrupted, not automatically replayed.
- [x] Implement cooperative cancellation, local subprocess termination, and remote Actions cancellation requests.
- [x] Implement graceful shutdown, interruption records, and one-time telemetry teardown.
- [x] Emit completed acceptance-attempt traces and use authorized bounded Neatlogs readback during recovery; preserve cancellation checks and labeled local fallback.
- [x] Reconcile PR side effects using a stable branch/marker and publication lease; lost-response retry is mock-tested.
- [x] Implement explicit preview/apply retention with checked cleanup paths and protected active/publishable runs; see `backend/RETENTION.md`.
- [x] Test competing claims, slow-operation heartbeats, expired-owner fencing, persisted submissions, and cooperative cancellation.
- [x] Verify real worker kill/restart at all fixture agent stages, lease fencing, HTTP cancellation, and API restart; isolated live-process evidence is saved.
- [x] Verify actual GitHub Actions cancellation; remote run 38177020201 finished cancelled.
- [x] Verify real Windows Ctrl+Break shutdown and hard interruption during an outstanding live Claude request, using isolated workers and saved evidence.
- [x] Verify hosted Linux SIGINT/SIGTERM lifecycle, restart/cancellation and SIGTERM during blocked localhost HTTP I/O; saved reports under `evidence/lifecycle-linux/38225586443/`.
- [ ] Verify actual paid-provider graceful shutdown separately; current blocked-I/O evidence uses a local provider fixture.
- [x] Verify Windows SIGBREAK during real blocked localhost HTTP I/O; preserve interruption and uncertain reservation without transport retry. This is a local provider fixture, not a paid-provider shutdown result.
- [x] Deploy and successfully run credential-free hosted Linux lifecycle and blocked-I/O checks; actual public-host acceptance remains separate.

## Why a worker

Repository preparation, model calls, and tests take minutes. The HTTP request should return immediately, while a separate Python process executes the job. FastAPI `BackgroundTasks` alone does not provide a durable queue or restart recovery. Use SQLite for the hackathon, with one worker and concurrency one; Redis/Celery are unnecessary for this scope.

Implemented commands (use the project virtual environment):

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -m backend worker
.\.venv\Scripts\python.exe -m backend run <issue-url>
```

The CLI `run` command only enqueues and returns the run ID; it neither waits nor claims a job. The separate worker executes it through the same queue/lease mechanism. Browser submissions preserve connected-user ownership; operator CLI submissions do not verify that browser path.

## Durable queue and ownership

Use `runs`, `attempts`, `events`, and `jobs` tables. A job includes run ID, available time, owner, lease expiry, heartbeat, execution count, cancellation flag, and last error. Store timestamps in UTC; use SQLite transactions and a busy timeout. Keep transactions short and never hold them across model/network/subprocess calls.

Claim an eligible job atomically inside a transaction. Only the current owner may heartbeat, update execution state, or finalize it. Use an ownership token/fencing counter to reject a worker whose lease expired. Initial proposed heartbeat is 10 seconds and lease is 60 seconds; configure these and renew during slow model calls and tests, not only between stages.

Persist state transitions, attempt results, and events before moving to the next step. Write artifact files using temporary files and atomic replacement; store their digest and path in the database. Artifacts referenced by a state update must already exist.

## Restart behavior and delivery guarantees

At startup, detect expired jobs. Do not blindly replay interrupted stages. Mark the run `interrupted`, reconcile checkout/head, completed artifact records, and any PR side effects, then resume only from an explicitly safe stage or require a fresh run. For the first release, recording interruption and allowing an operator rerun is acceptable; full transparent resume is not a claimed capability.

Publication must survive a crash after GitHub accepts the PR but before the database records it. Use a stable branch and run marker, query for an existing matching PR first, and reuse it. Verify that its head matches the approved patch. SQLite queues provide recoverable ownership, not exactly-once external side effects.

Agent recovery retries are distinct from job restarts and transient transport retries. Keep separate counters, deadlines, and retryable error categories. Authentication, invalid configuration, unsupported repositories, and exhausted budgets fail immediately with actionable messages.

## Cancellation and shutdown

Check cancellation before model calls, edits, tests, retries, pushes, and PR creation. Terminate a test's process tree on timeout or cancellation; retain bounded logs. Once an external write has begun, reconcile its outcome before reporting the run cancelled. Cancellation must never erase an already created PR from the run record.

On worker shutdown, stop claiming jobs, request cooperative cancellation or allow a bounded grace period, save interruption status, finish spans, and flush/shut down neatlogs once. A crash leaves the lease for startup reconciliation. Clean up only resolved paths inside the run workspace; retain failed artifacts for inspection according to an explicit retention policy.

## Observability and acceptance

Initialize telemetry once per worker process. Each issue run has an independent workflow root, with attempt/agent/tool children; independent concurrent jobs must not share trace context. Pass context explicitly to any new execution threads when needed. Polling reads committed state; SSE, if implemented, reads stored events and supports reconnect with event IDs.

Worker validation includes competing claims, heartbeat during a long operation, expired-owner writes rejected, kill/restart after each stage, cancellation during tests, API restart while a job runs, budgets across retries, and a crash between PR creation and persistence. Prove a duplicate delivery cannot create a second PR.

Deployment gate: GitHub App identity, user-scoped history/authentication, queue capacity limits and restricted test execution are implemented. Actual public-host acceptance, backups/restore, trusted proxy configuration and broader operational verification remain pending.

## Controlled PR publication implementation

- [x] Explicit operator-authenticated API and CLI publication, exact verified content checks, and stale-base rejection.
- [x] Operator-owned source/fork permission checks, stable branch, draft PR, and SQLite publication lease.
- [x] Mocked GitHub tests cover retry after a lost PR response, branch conflicts, changed artifacts, and concurrent publication.
- [x] Live controlled-fork draft PR published and saved: [davre001/kokon #1](https://github.com/davre001/kokon/pull/1).
- [x] GitHub App authentication and publication verified for the controlled connected-user trial; broader users/repositories remain unverified.

Publication runs as a bounded explicit API/CLI operation; the agent pipeline remains in the separate SQLite-backed worker. See [publication instructions](backend/PUBLICATION.md). The operator and one controlled connected-user flow are live-verified; broader multi-user/public-deployment acceptance remains pending.

## Next work in order

1. Demonstrate successful unseeded recovery on fork issue #7 after the daily admission reset; the latest real attempts failed and remain unchecked.
2. Finish actual paid-provider graceful shutdown verification. Windows blocked-localhost I/O and real provider hard interruption are separate evidence; Linux reports are tracked in backend/LIFECYCLE_VERIFICATION.md.
3. Verify disconnect fencing during a real in-flight publication; normal connected-user publication, browser disconnect/history and controlled publication-crash reconciliation are already verified separately.
4. Inspect the existing Render API and complete hosted worker provisioning, then verify HTTPS cookies/origins, trusted proxy and edge timeouts, private storage/backups, second-user isolation, restore and external logs/traces. Render is now live with basic health/proxy checks; full hosted acceptance remains pending.
5. Reconcile actual provider/Actions/storage billing against the observed model-cost samples. Original cfo.ai forecasting assumptions remain labelled.

Entire target context, reviewed gallery/slider revisions, local credential/pattern auditing and queue/HTTP limits are implemented and verified within their recorded scopes. Graph/Brain, arbitrary repository support and upstream contributions are optional extensions. Submission screenshots/video/packaging are deferred at the user's request.

## GitHub App backend milestone

- [x] OAuth connect/callback with browser-bound one-time state and S256 PKCE.
- [x] Encrypted server-side user credentials, expiring opaque sessions, secure production cookies, CSRF checks, and exact-origin CORS.
- [x] GitHub App installation/repository permission checks and per-user run ownership.
- [x] User-scoped worker/publication credentials; local operator PAT is never substituted for a visitor.
- [x] Disconnect invalidation, cooperative cancellation, publication/disconnect fencing, and signed authorization-revoked webhook.
- [x] Tests for OAuth replay, session expiry, secure cookies, CSRF, cross-user access, installation permissions, and revocation.
- [x] Register/configure the actual GitHub App and complete live browser-login and installed-repository acceptance on the reviewed fork.
- [x] Wire landing-page connection and workspace UI to these backend endpoints.

GitHub App code and the controlled connected-user issue-to-PR trial are verified; additional live acceptance is listed above. [GitHub App setup](backend/GITHUB_APP.md) records the required settings and current limitations. Expired sessions require reconnection; automatic token refresh is not implemented. The reviewed public-source allowlist/recipes and controlled user-owned publication policy still apply.

- [x] Controlled live publication crash/reconciliation: PR #6 recovered after process kill with one PR-creation POST. Isolated database and clock-advanced lease expiry; deterministic fixture review, no model calls. See [scope and report](backend/LIFECYCLE_VERIFICATION.md).
