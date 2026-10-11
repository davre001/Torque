# Backend implementation progress

Workspace update: `/workspace` now uses real session, repository, submit/status/history,
cancel/publish, and confirmed-disconnect endpoints. Landing Connect GitHub starts OAuth.
TypeScript and HTTP route checks pass. The connected-user issue-to-PR trial is verified; browser history/disconnect acceptance remains pending.

## Overall progress checklist

- [x] Add reviewed gallery keyboard acceptance and source/input guards for the current fork revision; local baseline and positive-fixture calibration pass.
- [ ] Push the updated runner workflow and verify gallery acceptance on hosted Linux before a fresh issue-to-PR trial.

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
- [x] Add pinned source snapshots, atomic artifacts, and isolated Docker/remote Actions test execution.
- [x] Add Neatlogs worker lifecycle and prepare independent kokon browser acceptance tests.
- [x] Add GitHub-hosted Linux runner workflow and backend adapter (mock-tested).
- [x] Publish/configure remote workflow and verify actual Linux/browser acceptance results.
- [x] Implement configuration preflight; live provider and destination access verified by the demo (automated live probes remain optional).
- [x] Implement typed records, SQLite persistence, and durable job ownership.
- [x] Implement and verify the separate worker lifecycle.
- [x] Implement repository tools and isolated test execution.
- [x] Implement Investigator, Implementer, Verifier, and local-artifact Recovery; recovery tested with controlled fixtures.
- [x] Verify real model tracing and authenticated failure-trace readback in a controlled live recovery drill.
- [ ] Obtain genuine Entire runtime context evidence.
- [x] Implement verified, idempotent branch/PR publication.
- [x] Connect the authenticated workspace to actual API state and keep simulations outside the real run path.
- [x] Complete a live connected-user run with an installed supported source repository; evidence is in `evidence/github-app/`.
- [x] Pass 115 automated tests and complete operator and connected-user issue-to-PR demonstrations.
- [x] Document runnable setup and export sanitized completed demo evidence.
- [x] Verify live browser history after refresh/relogin and confirmed disconnect; user confirmed the post-disconnect Connect fix.
- [x] Implement retention cleanup and validate preservation/deletion with disposable fixtures; live preview selects no old runs.
- [x] Verify isolated live-process restart/cancellation and actual GitHub Actions cancellation; see `backend/LIFECYCLE_VERIFICATION.md`.
- [x] Verify Windows Ctrl+Break shutdown and live provider hard interruption with isolated-process evidence.
- [ ] Finish Linux signals, blocked-provider graceful shutdown, and live publication crash/reconciliation acceptance.
- [ ] Complete the broader credential audit and public queue/spending controls before deployment.
- [ ] Verify recovery on a live GitHub repository; controlled seeded recovery is already saved.
- [ ] Review a fresh demo task/revision after the fork PR merge; arbitrary repositories remain unsupported.
- [x] Save the controlled hosted failure/recovery comparison and finalized readbacks.
- [ ] Finish dashboard screenshots, demo video, and submission packaging.

Design: [implementation](backend_implementation.md), [background worker](background_worker.md), [integrations](integration.md).

Python source lives in `backend/`; plans live at the root. The separate SQLite worker,
pinned source download, Gemini investigation/review, Claude patch, and remote Linux browser
tests have completed a live run. All three acceptance assertions passed and the verified
patch was published as [draft PR #1](https://github.com/davre001/kokon/pull/1).
Commands are in [backend/README.md](backend/README.md). Finalized trace readback and
controlled hosted recovery are saved in [recovery evidence](backend/NEATLOGS_RECOVERY.md).
The Claude-only connected-user trial completed as [PR #3](https://github.com/davre001/kokon/pull/3), now merged; see [user-run evidence](evidence/github-app/README.md). Current routing uses Claude for all roles, within one shared budget. Runtime Entire context remains pending.

Runtime database, checkouts, and logs will live under ignored `var/`. Selected sanitized run evidence belongs in `evidence/runs/`. Tests will be implemented alongside actual behavior.

## Controlled PR publication implementation

- [x] Explicit operator-authenticated API and CLI publication, exact verified content checks, and stale-base rejection.
- [x] Operator-owned source/fork permission checks, stable branch, draft PR, and SQLite publication lease.
- [x] Mocked GitHub tests cover retry after a lost PR response, branch conflicts, changed artifacts, and concurrent publication.
- [x] Live controlled-fork draft PR published and saved: [davre001/kokon #1](https://github.com/davre001/kokon/pull/1).
- [x] GitHub App authentication and publication verified for the controlled connected-user trial; broader users/repositories remain unverified.

Publication runs as a bounded explicit API/CLI operation; the agent pipeline remains in the separate SQLite-backed worker. See [publication instructions](backend/PUBLICATION.md). The operator and one controlled connected-user flow are live-verified; broader multi-user/public-deployment acceptance remains pending.

## Next work in order

1. Browser history/disconnect/reconnection is user-verified. Finish live publication/disconnect fencing acceptance.
2. Retention, local restart/API-restart/cancellation, remote cancellation, Windows Ctrl+Break, and live provider hard interruption are verified. Finish Linux signals, blocked-provider graceful shutdown, and live publication crash/reconciliation before public deployment; see [scope and evidence](backend/LIFECYCLE_VERIFICATION.md).
3. Capture genuine Entire target-repository runtime context if retained in scope. Development checkpoints are verified; Graph/Brain remains optional.
4. Demonstrate recovery on a live GitHub repository; the saved hosted-recovery drill deliberately seeded its first failure.
5. Audit credential exclusion across responses, sandbox environments, Git history, traces, and evidence; add public queue/spending limits before deployment.
6. Review a fresh demo task/revision: the merged fork PR changed the default branch, and the runner deliberately rejects revisions outside its reviewed scope.
7. Update cfo.ai assumptions from measured usage, then capture dashboard screenshots, demo video, and final submission links.

Evidence baseline (October 11, 2026): 115 automated tests passed. Operator PR #1, connected-user run `b220ce7e5cda4e14963c74fc04ad8711` and PR #3, finalized application readbacks, and a controlled hosted recovery drill are saved. PR #3 is now merged. Browser disconnect/history, runtime Entire context, broader repository support, and public deployment acceptance remain pending.

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
