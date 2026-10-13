# Torque deployment status and procedure

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

## Saved hosting inspection and remaining gates

The saved Render inspection identifies the existing Oregon/free Python service, automatic `main` deployments, and an empty dashboard health-check path despite a responding `/health`. `render.yaml` remains a proposed configuration rather than the deployed service description. The last saved GitHub review inspected 47 workflow runs and found no targeted agent-worker execution. These are dated observations, not fresh account queries.

Neon tools are now available in this session, superseding older notes that the connector was absent. No database query, account mutation, credential inspection, dispatch, or deployment was performed for this documentation update.

- [x] Implement the same-origin proxy, shared PostgreSQL storage, schema-2 migration, private artifacts, targeted worker and bounded manual reconciliation.
- [x] Record basic deployed frontend/API connectivity and isolated Neon concurrency/storage/restore verification.
- [x] Record user-reported schema-2/runtime-grant SQL results; independent current verification remains separate.
- [ ] Take and verify a fresh schema-2 encrypted backup; confirm off-machine custody.
- [ ] Provision/verify the protected Actions environment and run one real assigned hosted job.
- [ ] Verify production login, second-user isolation, supported repository execution, artifact retrieval/retention, cancellation and explicit idempotent publication.
- [ ] Exercise compatible restore/rollback, host/proxy limits, deployed credential/log checks, quotas and billing.
- [ ] Verify successful unseeded recovery, paid-provider graceful shutdown and publication/disconnect fencing.

The [README](README.md) is now rewritten and published with workflow/integration diagrams and evidence links at commit [4317988](https://github.com/davre001/Torque/commit/43179880579ef3d646b33fe38b5dee00c8cf9574), with Entire checkpoint `01M4SE2FKCRGJ39A5YBTS0HE5K`. Documentation publication does not verify runtime deployment.

## Detailed deployment procedure

The following procedure retains individual implementation and acceptance checks. Historical provider/account observations are not refreshed by this documentation edit.

## Hosting layout

| Component | Where | Purpose |
| --- | --- | --- |
| Next.js frontend | Vercel, project root `frontend/ui` | Landing page, GitHub login entry, workspace, progress and history |
| Python API | Render free Web Service, repository root | Authentication, permissions, admission, history, cancellation and explicit publication |
| PostgreSQL database | Neon free plan, subject to current quotas | Shared durable users, encrypted credentials, sessions, queue, leases, runs, events and budgets |
| Agent worker | GitHub Actions in `davre001/Torque`, new workflow | Start a separate Python process for one assigned run, then exit |
| Independent acceptance tests | Existing `torque-remote-tests.yml` on GitHub Actions | Run reviewed tests separately from the credential-bearing agent worker |
| Durable run artifacts | Private PostgreSQL artifact records in Neon | Preserve verified patches and evidence after Actions runners disappear; 2 MiB per record |
| Tracing | Existing Neatlogs project | Workflow spans, failure investigation and recovery readback |

The worker code stays in `backend/`. Deployment does not require moving it into
another folder. The new agent workflow is separate from the existing test and
lifecycle workflows. Do not deploy a continuously running worker on Render free.

Render free services have ephemeral filesystems and sleep after inactivity; free
Render PostgreSQL expires after 30 days. This plan therefore uses an external
database. Verify all selected providers' quotas and eligibility before provisioning.
Sources: [Render free limits](https://render.com/docs/free),
[Neon free plan](https://neon.com/blog/neon-free-plan-1-gb-per-project).

## 1. Prepare the repository before deploying

- [x] Implement PostgreSQL configuration (`TORQUE_DATABASE_URL`) and transactional schema migrations; preserve local SQLite.
- [x] Route storage, OAuth/session persistence, publication, queue claims, daily reservations and HTTP counters through the database boundary.
- [x] Implement atomic admission and exclusive leases with a PostgreSQL transaction advisory lock; isolated Neon concurrency verification passed; production worker acceptance remains pending.
- [x] Add `worker --run-id` that claims only the assigned job.
- [x] Implement durable dispatch bookkeeping, stable request IDs and bounded manual reconciliation.
- [x] Preserve shared-database cancellation checks, lease expiry and signal handling in targeted workers.
- [x] Implement private database artifacts, per-record size limits, immutable hashes and retention.
- [x] Retrieve verified contents for cloud publication without the worker's local files.
- [x] Add the production API proxy and credential-free cookie/redirect/origin contract checks.
- [ ] Verify complete OAuth/session behavior in a real production browser.
- [x] Verify PostgreSQL migrations, concurrent admission/claims, cancellation, lease expiry, artifact persistence, HTTP counters and publication fencing in disposable Neon schemas (two integration tests passed).
- [ ] Verify the complete deployed worker/artifact-retention/publication flow; local contract checks do not establish deployed acceptance.
- [x] Add `preflight --cloud-probe` for bounded database and workflow-access checks without printing secrets.

Implementation details and limits: [cloud preparation](backend/CLOUD_PREPARATION.md).
Checked items above describe implemented code, not successful cloud deployment.

Do not replace a SQLite filename with a PostgreSQL URL and expect the existing
backend to work. This is a storage and execution migration.

## 2. Create the shared database

- [x] Create/connect the Neon project.
- [ ] Align the Render region with this database when provisioning the API in Phase 4.
- [x] Review published free-plan and restore limitations.
- [ ] Confirm the account's actual storage and compute quotas in Neon before public release.
- [x] Save the TLS connection string in ignored local `.env` without exporting it in evidence.
- [x] Provision a DML-only runtime role and save the owner URL separately as `TORQUE_MIGRATION_DATABASE_URL`.
- [x] Apply migrations and test them in isolated staging schemas on the initially empty database.
- [x] Back up local SQLite with the online backup API, encrypt it, and verify restored integrity.
- [ ] Optional: import local history only if needed, preserving user ownership, artifact hashes and encrypted credentials. Current decision: retain the encrypted SQLite backup; no history has been imported into Neon.
- [x] Configure local API and worker to read the same restricted `TORQUE_DATABASE_URL`.
- [ ] Provision that runtime URL to Render and protected Actions secrets during Phases 4–5; exclude the migration owner URL.
- [x] Verify encrypted PostgreSQL export and isolated restore of all 14 tables; archive and evidence paths are documented below.
- [ ] Store encrypted backups off-machine and keep their encryption key separately before public release.

Database setup and restore commands: [database operations](backend/DATABASE_OPERATIONS.md).
Neon's published limits can change; verify your dashboard allowance. Its recent
[free-storage announcement](https://neon.com/blog/neon-free-plan-1-gb-per-project)
updates older storage figures. Restore history is bounded, so retain independent
encrypted backups; see [Neon free-plan limits](https://github.com/neondatabase/website/blob/main/content/faqs/free-plan-limits-and-quotas.md).

## 3. Verify private database artifact storage

- [x] Verify `artifact_records` exists in the configured Neon deployment database; no separate storage account is required. Production deployment remains pending.
- [x] Verify the configured runtime role has artifact DML access, no schema CREATE permission, and the table has no PUBLIC grants. Database credentials remain server-only.
- [x] Check representative saved JSON artifacts against the 2 MiB record limit: 24 records, largest 6,107 bytes. Verify enforcement of the independent 8 MiB per-run bound.
- [ ] Confirm available storage in the Neon account dashboard before release; record and run caps do not impose a global database quota.
- [x] Verify durable writes, immutable hashes, tamper rejection, publication retrieval without local files, and retention in an isolated Neon schema.
- [x] Scan local tracked/evidence files and reachable Git blobs for current credentials and common secret patterns; no matches found. Include durable database artifacts in subsequent credential audits.
- [ ] Repeat artifact retrieval and retention through the deployed API/Actions worker in Phase 9.
- [ ] Audit deployed public evidence and logs for prompts, source archives and credentials before release. Local credential scanning and telemetry masking do not establish deployed log acceptance.

Evidence: [private artifact checks](evidence/deployment/private-artifact-checks.json).
The database integration trial used fixture content, made no provider calls or
GitHub publication requests, and removed its temporary schema. Retention keeps
publishable runs and removes expired terminal-run artifacts while preserving history.

Actions artifacts may supplement demo evidence, but are not the default durable
publication store: they have retention and access constraints. API and worker
local disks are temporary staging space only.

## 4. Deploy the API to Render

Configuration is prepared in [render.yaml](render.yaml); follow the
[Render deployment steps](backend/RENDER_DEPLOYMENT.md). The configured existing
service is https://torque-sxqr.onrender.com and its health route passed. Inspect
the existing service before making changes; do not create a duplicate service.

- [ ] Connect `davre001/Torque` to Render and create a **Web Service**.
- [ ] Use the repository root as the service root so `backend` imports and reviewed test files resolve correctly.
- [ ] Choose a Python version compatible with the project's tested environment.
- [ ] Build with `pip install -r requirements.txt`, after adding the PostgreSQL/storage dependencies to that manifest.
- [ ] Start with `python -m uvicorn backend.api:app --host 0.0.0.0 --port $PORT`.
- [x] Verify the live API `/health` route returns HTTP 200 and `status: ok`; the Render dashboard health-check setting still needs account inspection.
- [ ] Add shared database/storage configuration through Render's secret environment settings.
- [ ] Add GitHub App client configuration, session encryption key and webhook secret as required by the implemented routes.
- [ ] Add a narrowly scoped server-side workflow dispatch credential; never use a visitor's token for deployment orchestration.
- [ ] Leave `TORQUE_OPERATOR_TOKEN` empty in production and enable `TORQUE_PUBLIC_MODE=1` only once production HTTPS/origin settings are valid.
- [ ] Preserve repository allowlists, reviewed recipes, request limits and daily spending limits.
- [ ] Confirm no SQLite or local artifact path remains authoritative in production.
- [x] Record the configured Render HTTPS origin: https://torque-sxqr.onrender.com; the deployed Vercel proxy reaches its authentication route.

The API must not execute long agent runs inside a request. It accepts a job,
dispatches its worker and returns a run ID. Expect cold starts on Render free;
the worker must continue independently while the API sleeps.

## 5. Deploy the agent worker to GitHub Actions

- [x] Add the manually/API-dispatched `torque-agent-worker.yml` with assigned run ID and request ID inputs; hosted activation remains pending.
- [x] Configure checkout with persisted credentials disabled; production branch protection and revision policy still require account verification.
- [x] Configure Python dependency installation and `python -m backend worker --run-id`; live cloud execution remains pending.
- [ ] Store database, provider, Neatlogs and required encryption secrets in protected Actions settings.
- [x] Configure read-only workflow contents permission, concurrency one and authoritative database leases.
- [x] Configure a 25-minute worker job timeout; verify graceful finalization in the hosted trial.
- [ ] Keep target repository code out of credential-bearing execution. Continue using the isolated acceptance-test workflow for untrusted code.
- [ ] Confirm the acceptance workflow can be dispatched and polled from the agent job with appropriately scoped credentials.
- [ ] Upload durable artifacts before finalizing a verified run; flush Neatlogs before process exit.
- [ ] Exercise cancelled/expired jobs and verify they become interrupted without automatic paid replay.
- [ ] Monitor Actions usage and storage allowances; do not claim unlimited free execution.

GitHub documents token behavior for workflow triggers in
[Triggering a workflow](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
Keep worker secrets separate from the credential-free test workflow.

## 6. Deploy the frontend to Vercel

- [x] Connect `davre001/Torque` to the existing Vercel project `torque`.
- [x] Set **Root Directory** to `frontend/ui` and select Next.js.
- [x] Build the committed frontend successfully on Vercel; local production build also passes.
- [x] Confirm server-only production proxy setting names are present; verify their values against the API during hosted acceptance.
- [x] Implement relative same-origin browser calls and login entry points; production browser verification remains pending.
- [ ] Never put database URLs, provider keys, App secrets or encryption keys in `NEXT_PUBLIC_*` variables or client code.
- [x] Deploy and record the stable production URL: https://torque-pied.vercel.app. Configure the App callback against this origin during hosted acceptance.
- [ ] Verify landing page, workspace, history and error states on the deployed frontend.

External proxying is supported through
[Vercel rewrites](https://vercel.com/docs/routing/rewrites), but cookie, redirect,
host and origin behavior must be implemented and tested for Torque. A rewrite
alone does not establish successful authentication.

## 7. Configure production GitHub login and request boundaries

- [ ] Set `TORQUE_FRONTEND_ORIGIN` to the stable Vercel HTTPS origin.
- [ ] Set `GITHUB_APP_CALLBACK_URL` to `https://<frontend-production-host>/api/auth/github/callback` through the implemented proxy.
- [ ] Update the GitHub App homepage and callback settings to these production URLs.
- [ ] Configure the public webhook URL and signature secret if webhook delivery is enabled.
- [ ] Verify forwarded host/protocol handling and backend host allowlisting through the proxy; trust only the configured proxy path.
- [ ] Verify Secure, HttpOnly, host-only cookies and CSRF/origin checks in a real browser.
- [ ] Verify login, refresh, disconnect, immediate reconnect and persistent history.
- [ ] Verify two different users cannot read, cancel or publish each other's runs.
- [ ] Confirm production API routes reject operator bearer access and expose minimal health information.

The current SameSite=Lax cookie policy does not support ordinary credentialed
cross-site requests between unrelated `vercel.app` and `onrender.com` origins.
Use the tested same-origin proxy design, or same-site custom domains if available.
Do not disable state or CSRF validation to make login succeed.

## 8. Configure agent integrations

- [ ] Set the selected provider mode and model alias; verify real provider availability within existing budgets.
- [ ] Configure conservative token cost rates and retain the existing call/token/time/dollar caps.
- [ ] Set `TORQUE_RUNNER=github-actions` and the reviewed Actions repository/ref configuration.
- [ ] Enable only repositories with calibrated immutable acceptance profiles.
- [ ] Configure Neatlogs ingest and readback credentials separately; verify an actual application trace.
- [ ] Decide how runtime Entire authentication is securely provisioned on an ephemeral worker. Local CLI login is not automatically available in Actions.
- [ ] Keep `TORQUE_ENTIRE_CONTEXT=0` until hosted runtime access is verified; do not describe it as enabled when unavailable.
- [ ] Retain development checkpoint evidence separately from runtime repository context.

## 9. Verify staging, then production

- [ ] Run preflight against staging without exposing secrets.
- [ ] Submit one authorized unresolved issue through the browser and follow real persisted progress.
- [ ] Verify baseline reproduction, implementation, every acceptance criterion and review before publication.
- [ ] Confirm the worker finishes while Render is idle or restarted.
- [ ] Confirm history and artifacts survive API redeploys and runner deletion.
- [ ] Test cancellation, worker interruption and dispatch reconciliation.
- [ ] Review the verified patch, explicitly publish a controlled draft PR, and confirm retry does not create duplicates.
- [ ] Audit deployed logs, database access and selected Neatlogs payloads for credentials.
- [ ] Verify cold-start behavior, rate limits, daily admission limits and proxy request boundaries.
- [ ] Demonstrate genuine recovery only when a real failed attempt is followed by an independently passing attempt; retain truthful failed evidence otherwise.
- [ ] Repeat smoke checks using production settings before allowing broader access.

## 10. Operations and rollback

- [ ] Record frontend/API URLs, worker workflow, deployed commit and migration version without secrets.
- [ ] Define database backups, private artifact retention and restore ownership.
- [ ] Rehearse restoring database and artifact references together.
- [ ] Document how to stop new admissions and cancel running workflows without refunding uncertain provider usage.
- [ ] Roll back API/frontend/worker revisions only to versions compatible with the deployed schema.
- [ ] Monitor database/storage/Actions quotas and model spending; distinguish estimates from actual bills.
- [ ] Rotate deployment credentials when needed and retain the session encryption key required to decrypt existing user credentials.

## Deployment completion

- [ ] Independently verify current schema-2 PostgreSQL migration/runtime grants; user-reported checks passed, and saved automated checks cover schema 1.
- [x] Private database artifact implementation and isolated Neon verification passed; deployed retrieval remains pending.
- [x] Render API live with passing public health and trusted proxy entry checks; deployed revision/runtime configuration and full acceptance remain pending.
- [ ] Targeted Actions worker live.
- [x] Vercel frontend deployed and READY; production browser/API acceptance remains pending.
- [ ] Production GitHub login and per-user permissions verified.
- [ ] End-to-end authorized run and explicit publication verified.
- [ ] Backup, interruption and rollback checks passed.

Related implementation and release gates:
[backend readiness](backend/DEPLOYMENT_READINESS.md),
[integration checklist](integration.md),
[worker checklist](background_worker.md).
