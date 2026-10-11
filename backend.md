# Backend implementation progress

Workspace update: `/workspace` now uses real session, repository, submit/status/history,
cancel/publish, and confirmed-disconnect endpoints. Landing Connect GitHub starts OAuth.
TypeScript and HTTP route checks pass; connected-user browser acceptance remains pending.

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
- [x] Implement provider adapters, bounded agent roles, patch validation, and fixture-tested verification/recovery.
- [x] Add pinned source snapshots, atomic artifacts, and Docker-only test execution interface.
- [x] Add Neatlogs worker lifecycle and prepare independent kokon browser acceptance tests.
- [x] Add GitHub-hosted Linux runner workflow and backend adapter (mock-tested).
- [x] Publish/configure remote workflow and verify actual Linux/browser acceptance results.
- [x] Implement configuration preflight; live provider and destination access verified by the demo (automated live probes remain optional).
- [x] Implement typed records, SQLite persistence, and durable job ownership.
- [x] Implement and verify the separate worker lifecycle.
- [x] Implement repository tools and isolated test execution.
- [x] Implement Investigator, Implementer, Verifier, and local-artifact Recovery; recovery tested with controlled fixtures.
- [ ] Verify real model tracing and authenticated failure-trace readback.
- [ ] Obtain genuine Entire runtime context evidence.
- [x] Implement verified, idempotent branch/PR publication.
- [x] Connect the authenticated workspace to actual API state and keep simulations outside the real run path.
- [ ] Complete a live connected-user run with an installed supported source repository.
- [x] Pass 74 automated tests and complete the controlled issue-to-PR demonstration.
- [x] Document runnable setup and export sanitized completed demo evidence.
- [ ] Finish dashboard screenshots, recovery comparison, and submission packaging.

Design: [implementation](backend_implementation.md), [background worker](background_worker.md), [integrations](integration.md).

Python source lives in `backend/`; plans live at the root. The separate SQLite worker,
pinned source download, Gemini investigation/review, Claude patch, and remote Linux browser
tests have completed a live run. All three acceptance assertions passed and the verified
patch was published as [draft PR #1](https://github.com/davre001/kokon/pull/1).
Commands are in [backend/README.md](backend/README.md). Neatlogs dashboard readback,
runtime Entire context, and the connected-user frontend remain pending.

Runtime database, checkouts, and logs will live under ignored `var/`. Selected sanitized run evidence belongs in `evidence/runs/`. Tests will be implemented alongside actual behavior.

## Controlled PR publication implementation

- [x] Explicit operator-authenticated API and CLI publication, exact verified content checks, and stale-base rejection.
- [x] Operator-owned source/fork permission checks, stable branch, draft PR, and SQLite publication lease.
- [x] Mocked GitHub tests cover retry after a lost PR response, branch conflicts, changed artifacts, and concurrent publication.
- [x] Live controlled-fork draft PR published and saved: [davre001/kokon #1](https://github.com/davre001/kokon/pull/1).
- [ ] GitHub App authentication and publication for connected visitors.

Publication runs as a bounded explicit API/CLI operation; the agent pipeline remains in the separate SQLite-backed worker. See [publication instructions](backend/PUBLICATION.md). The controlled single-operator flow is live-verified; the public multi-user flow remains pending.

## Next work in order

1. Implement GitHub App connect/callback/session/disconnect, secure server-side credentials, and per-user repository/run authorization for the requested visitor flow.
2. Connect the Next.js workspace to real submit/status/history/cancel/publish endpoints; show actual progress, errors, and PR URLs instead of simulation.
3. Resolve Neatlogs finalized application trace readback and implement authorized failure-trace retrieval. Export a genuine failure/recovery comparison; the successful demo had no recovery retry.
4. Implement genuine Entire target-repository context if required by the runtime plan. Development checkpoints already exist; Graph/Brain Continuous Memory remains optional.
5. Add workspace/artifact retention, broader restart/cancellation acceptance, and public-deployment limits before expanding beyond the reviewed kokon recipe.
6. Capture final screenshots and a short demo, update financial assumptions from measured usage, and complete submission evidence.

Evidence baseline (October 11, 2026): 74 automated tests passed; live issue-to-draft-PR demo completed. Automated live credential probes, public-user authentication, finalized trace readback, and broad repository support are not claimed complete.

## GitHub App backend milestone

- [x] OAuth connect/callback with browser-bound one-time state and S256 PKCE.
- [x] Encrypted server-side user credentials, expiring opaque sessions, secure production cookies, CSRF checks, and exact-origin CORS.
- [x] GitHub App installation/repository permission checks and per-user run ownership.
- [x] User-scoped worker/publication credentials; local operator PAT is never substituted for a visitor.
- [x] Disconnect invalidation, cooperative cancellation, publication/disconnect fencing, and signed authorization-revoked webhook.
- [x] Tests for OAuth replay, session expiry, secure cookies, CSRF, cross-user access, installation permissions, and revocation.
- [ ] Register/configure the actual GitHub App and complete live browser-login and installed-repository acceptance.
- [ ] Wire landing-page connection and workspace UI to these backend endpoints.

The earlier unchecked GitHub App items now refer to live acceptance and frontend integration. Backend code is implemented; [GitHub App setup](backend/GITHUB_APP.md) records the required settings and current limitations. Expired sessions require reconnection; automatic token refresh is not implemented. The reviewed public-source allowlist/recipes and controlled user-owned publication policy still apply.
