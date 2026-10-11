# Torque background worker plan

Status: proposed. [Backend overview](backend_implementation.md) defines the API and agent behavior; [integrations](integration.md) defines external access.

## Worker progress checklist

The worker is a separate process. FastAPI only submits jobs and reads state; it must not execute agents through `BackgroundTasks`.

Remote execution option: `TORQUE_RUNNER=github-actions` dispatches the reviewed kokon
acceptance workflow to GitHub-hosted Ubuntu. The local worker still owns jobs, model calls,
leases, and budgets; remote jobs only execute tests. See [setup](backend/REMOTE_RUNNER.md).
Live dispatch and browser acceptance are pending.

- [x] Select SQLite and one separate worker with concurrency one for the prototype.
- [x] Create `backend/worker.py` and `backend/store.py` placeholders.
- [x] Implement queue schema, atomic job claims, ownership tokens, and persisted worker state.
- [x] Implement `python -m backend worker`; CLI submissions enqueue for that worker.
- [x] Implement heartbeats during slow operations and reject expired-owner writes.
- [x] Enforce prototype concurrency one across competing worker processes.
- [x] Persist local attempt/test/recovery artifacts atomically before advancing pipeline state.
- [x] Separate bounded transport retries from the maximum two agent recovery retries.
- [ ] Persist attempt outcomes and atomic artifact records before advancing stages.
- [x] Detect expired jobs on claim/startup and mark interrupted without replay.
- [ ] Bound job restarts, transport retries, and agent recovery independently.
- [ ] Implement cancellation checks and test-process-tree termination.
- [ ] Implement graceful shutdown, interruption records, and one-time telemetry teardown.
- [ ] Reconcile PR side effects after crashes and prevent duplicate PR creation.
- [ ] Implement workspace retention and checked cleanup paths.
- [ ] Verify competing claims, long-running leases, kill/restart, cancellation, and API restart behavior.

## Why a worker

Repository preparation, model calls, and tests take minutes. The HTTP request should return immediately, while a separate Python process executes the job. FastAPI `BackgroundTasks` alone does not provide a durable queue or restart recovery. Use SQLite for the hackathon, with one worker and concurrency one; Redis/Celery are unnecessary for this scope.

Proposed commands, to be implemented:

```powershell
python -m uvicorn frontend.app:app --host 127.0.0.1 --port 8000
python -m backend worker
python -m backend run <issue-url>
```

CLI execution uses the same persisted jobs and coordinator, and must not race with an already running worker. Document whether the CLI waits for the worker or claims its own job through the identical lease mechanism.

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

Deployment gate: one trusted local operator initially. Public use requires per-tenant storage/authentication, queue capacity limits, isolated sandboxes, operational recovery, and GitHub App credentials; these are later work.
