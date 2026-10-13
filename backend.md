# Torque backend progress

## Current development status - October 13, 2026

This update reflects repository code through `b6bff472404af9daf670b362b8cebb94b9fb7164` and saved evidence. It does not establish a new deployed revision or a new production acceptance result.

- The issue-to-PR pipeline, GitHub App sessions, owner-scoped run APIs, independent tests, explicit publication, and durable queue are implemented.
- Controlled reduced-motion and gallery runs published verified PRs: [connected-user PR #3](https://github.com/davre001/kokon/pull/3) and [gallery PR #5](https://github.com/davre001/kokon/pull/5). Both are recorded as merged; Torque's verification did not perform those merges.
- The current `davre001/kokon` remote recipe selects **slider-keyboard**, replacing the completed gallery task. Approved slider revisions are `218143b523252ee95c2368adc83fef95b324b156` and `513883a43ea33474431c933018b6267d08acb8f5`. The newer revision changes only a Gallery comment; slider HTML/CSS are unchanged.
- The October 13 local Edge baseline passed **1/5** groups: pointer/selection/media regressions passed, while semantics, keyboard bounds, sweep/focus, and descriptions failed. This reproduces the outstanding issue; it is not a successful agent fix. See [slider acceptance](tests/acceptance/slider/README.md).
- Earlier real slider trials exhausted three attempts without publishing. Successful unseeded recovery remains unverified. The separate [controlled recovery drill](evidence/recovery/ce1d5d570a144e608d98d49031579dd2/README.md) did pass after a deliberately seeded failure.
- Local SQLite and optional shared PostgreSQL are implemented, including private database artifacts and targeted Actions dispatch. User-provided SQL confirms schema 2 and restricted runtime grants; that is user-reported evidence. A fresh schema-2 encrypted backup and deployed worker acceptance remain pending.
- The last saved deployment inspection found a live Vercel frontend and Render API at `e582fb9`, with health/proxy/OAuth-entry boundaries passing. Later repository commits do not prove later deployment acceptance.
- The last saved broad validation reports **192 Python tests passed, five skipped**, TypeScript/proxy contracts, a production build, and Edge workspace fixtures. These are historical recorded results, not tests rerun for this documentation update.

[Product overview](README.md) ? [Saved deployment verification](evidence/deployment/current-verification.json) ? [Connected-user evidence](evidence/github-app/README.md) ? [Gallery publication](evidence/gallery/completed-publication.json)

## Backend implementation now in place

FastAPI exposes authenticated run submission/history/events, cancellation, repository discovery, and explicit publication. GitHub App tokens are encrypted server-side; user runs enforce ownership and repository access instead of substituting an operator token.

The API persists work rather than executing agents in request handlers. Workers claim durable leases, apply budget reservations, fetch reviewed source, run the baseline, invoke agents, execute independent tests, and persist redacted artifacts. Passing tests and model review are both required before publication.

The workspace shows repository readiness rather than setup controls. Schema-2 `repository_setups` support remains in the backend, but the current UI does not offer onboarding controls. Repository access alone does not authorize an arbitrary test command.

[Runtime guide](backend/README.md) ? [Backend plan](backend_implementation.md) ? [Publication](backend/PUBLICATION.md)

## Earlier implementation milestones and design history

The material below preserves earlier milestones and design decisions. Its old counts, proposed structures, and pending checks describe their original scope; the current status above takes precedence.

## Overall progress checklist

Current validation: 192 automated tests passed, five skipped (October 12, 2026). Public API request
boundaries and blocked-I/O shutdown are implemented and locally verified. Current
credential/pattern audit and Entire target context are verified. Linux workflow
execution passed (Actions `38225586443`); actual paid-provider and public-host checks remain separate gates.

- [x] Add reviewed gallery keyboard acceptance and source/input guards for the current fork revision; local baseline and positive-fixture calibration pass.
- [x] Push the updated runner workflow and reproduce the gallery baseline on hosted Linux (Actions `38183797125`); fresh issue-to-PR verification remains separate.

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
- [x] Obtain genuine Entire runtime context evidence from the mirrored fork and save live slider-run context artifacts.
- [x] Implement verified, idempotent branch/PR publication.
- [x] Connect the authenticated workspace to actual API state and keep simulations outside the real run path.
- [x] Complete a live connected-user run with an installed supported source repository; evidence is in `evidence/github-app/`.
- [x] Pass 115 automated tests and complete operator and connected-user issue-to-PR demonstrations.
- [x] Document runnable setup and export sanitized completed demo evidence.
- [x] Verify live browser history after refresh/relogin and confirmed disconnect; user confirmed the post-disconnect Connect fix.
- [x] Implement retention cleanup and validate preservation/deletion with disposable fixtures; live preview selects no old runs.
- [x] Verify isolated live-process restart/cancellation and actual GitHub Actions cancellation; see `backend/LIFECYCLE_VERIFICATION.md`.
- [x] Verify Windows Ctrl+Break shutdown and live provider hard interruption with isolated-process evidence.
- [x] Verify hosted Linux SIGINT/SIGTERM, restart/cancellation and graceful shutdown during blocked localhost provider-fixture I/O; Actions `38225586443`.
- [ ] Verify graceful shutdown during an actual paid-provider request; this remains separate from the local HTTP fixture and earlier hard-kill probe.
- [x] Audit current credential exclusion in local files/artifacts, response records and valid local Git history; implement atomic queue/spending controls.
- [x] Audit common secret patterns locally and current credential exclusion in three actual finalized Neatlogs traces (63 spans).
- [ ] Review host logs, unknown/rotated secrets outside scanned patterns and actual public deployment controls. Render basic health/proxy checks pass; hosted log/configuration review remains pending; see [deployment readiness](backend/DEPLOYMENT_READINESS.md).
- [ ] Verify recovery on a live GitHub repository; controlled seeded recovery is already saved.
- [x] Review fresh gallery and slider tasks/revisions after the fork PR merge; arbitrary repositories remain unsupported.
- [x] Save the controlled hosted failure/recovery comparison and finalized readbacks.
- [ ] Finish dashboard screenshots, demo video, and submission packaging.

Design: [implementation](backend_implementation.md), [background worker](background_worker.md), [integrations](integration.md).

Python source lives in `backend/`; plans live at the root. The separate SQLite worker,
pinned source download, Gemini investigation/review, Claude patch, and remote Linux browser
tests have completed a live run. All three acceptance assertions passed and the verified
patch was published as [draft PR #1](https://github.com/davre001/kokon/pull/1).
Commands are in [backend/README.md](backend/README.md). Finalized trace readback and
controlled hosted recovery are saved in [recovery evidence](backend/NEATLOGS_RECOVERY.md).
The Claude-only connected-user trial completed as [PR #3](https://github.com/davre001/kokon/pull/3), now merged; see [user-run evidence](evidence/github-app/README.md). Current routing uses Claude for all roles, within one shared budget. Runtime Entire target context is verified in the saved live slider artifacts.

Runtime database, checkouts, and logs will live under ignored `var/`. Selected sanitized run evidence belongs in `evidence/runs/`. Tests will be implemented alongside actual behavior.

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
