# Backend implementation progress

## Overall progress checklist

Checked items mean completed setup or verified behavior, not merely an existing placeholder. Update these lists with each implementation milestone; detailed acceptance criteria live in the linked plans.

- [x] Create the Python scaffold under `backend/`.
- [x] Draft backend, separate-worker, and integration plans at the project root.
- [x] Select a separate Python worker with a SQLite queue.
- [x] Create test/fixture and runtime artifact directories; ignore runtime files and Python caches.
- [x] Collect cfo.ai spreadsheet and screenshot evidence.
- [x] Implement root environment loading, typed states, and strict issue URL validation.
- [x] Implement SQLite history, events, idempotency, atomic claims, and expired-owner fencing.
- [x] Implement separate worker, heartbeat renewal, cancellation, and interrupted-job recovery.
- [x] Replace legacy API BackgroundTasks with authenticated queue/status/history routes.
- [x] Implement and test read-only GitHub issue lookup.
- [ ] Implement configuration and provider/GitHub preflight checks.
- [ ] Implement typed records, SQLite persistence, and durable job ownership.
- [ ] Implement and verify the separate worker lifecycle.
- [ ] Implement repository tools and isolated test execution.
- [ ] Implement Investigator, Implementer, Verifier, and Recovery.
- [ ] Verify real model tracing and authenticated failure-trace readback.
- [ ] Obtain genuine Entire runtime context evidence.
- [ ] Implement verified, idempotent branch/PR publication.
- [ ] Connect the frontend to actual API state and remove simulated results from the real run path.
- [ ] Complete automated checks and the issue-to-PR demonstration.
- [ ] Update runnable setup commands, export sanitized evidence, and prepare the submission.

Design: [implementation](backend_implementation.md), [background worker](background_worker.md), [integrations](integration.md).

Python source lives in `backend/`; design documents live at the root. The queue/API/worker milestone is implemented; agent and tool modules remain pending. Runnable commands and limitations are in [backend/README.md](backend/README.md). The worker currently fetches issue context and records an explicit incomplete-pipeline failure. It does not call models or create PRs.

Runtime database, checkouts, and logs will live under ignored `var/`. Selected sanitized run evidence belongs in `evidence/runs/`. Tests will be implemented alongside actual behavior.
