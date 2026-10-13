# Torque deployment plan

## Database verification update — October 13, 2026

User-provided Neon SQL results confirm schema version 2 and runtime role
`torque_runtime_4833357e53e3` with all four elevated role flags disabled,
SELECT/INSERT/UPDATE/DELETE on all 15 Torque tables (including repository_setups),
no CREATE on public schema, and USAGE on the events sequence. These are user-reported
checks, not an independent agent query. Fresh schema-2 encrypted backup and
production worker/end-to-end verification remain pending.


Status updated October 12, 2026: cloud preparation is implemented and the Vercel
frontend is deployed. Saved Neon database, encrypted restore and private artifact
checks passed in isolated schemas. Production API/worker and browser acceptance
are partly verified: the configured Render API is healthy and OAuth entry/proxy
boundaries pass. Worker execution and full browser acceptance remain unverified.
SQLite remains the local default; PostgreSQL is opt-in.
This plan excludes hackathon submission preparation.

## Current verified state and remaining gates

Connected-account verification: Render and GitHub are now accessible. The user
confirmed **Aaron's workspace** for Render. Service `srv-db6e8op42hec73bu7nd0`
is live on `e582fb9`, Python/free, repository root, branch `main`, region **Oregon**,
with automatic commit deployments. Its configured health-check path is empty;
set `/health` in the existing service dashboard. `render.yaml` remains a proposed
Frankfurt/manual-deploy configuration, not a description of the deployed service.
Verify Neon region before any regional migration; do not recreate the service.
No Render error-level logs were returned after the latest deployment finished.
GitHub CI [38296501216](https://github.com/davre001/Torque/actions/runs/38296501216)
passed for the same commit. All 47 repository workflow runs were inspected;
none used `torque-agent-worker.yml`, so hosted agent execution is not verified.
The available GitHub tools support reads but not secret provisioning or dispatch.
Neon is reported connected by the user but its tools are not exposed here yet.

- [x] Vercel project `torque` is connected to `davre001/Torque`, root `frontend/ui`, Next.js, production branch `main`, with automatic Git deployments enabled.
- [x] Production commit `e582fb90260bca3b5edeb88300ab277026facd9d` reached READY in deployment `dpl_A9Teim4ZBr7WmS7gawY76aqnCyKB`; stable URL: https://torque-pied.vercel.app. The earlier landing check returned HTTP 200 and Torque's title.
- [x] Required production Vercel settings are present: `TORQUE_BACKEND_ORIGIN`, `TORQUE_FRONTEND_ORIGIN`, `TORQUE_PROXY_SECRET`. Presence was checked without printing values; correctness and matching API settings remain unverified.
- [x] Configured Render API https://torque-sxqr.onrender.com returned HTTP 200 with `status: ok`. Authenticated Vercel session probing reached Torque and returned `GitHub login required`; OAuth entry returned 302 to GitHub; direct Render OAuth without the proxy secret returned 403.
- [x] Current local verification: 192 Python tests passed, 5 skipped; TypeScript and proxy cookie/redirect/origin/body-limit/secret-isolation checks passed; production Next.js build passed with network access for Google Fonts. Local tests disabled dotenv loading and did not access `.env`.
- [x] Edge workspace browser contract passed: simulated session, CSRF submission, recovery/progress, acceptance results, terminal polling, explicit publication result, persisted failure display, confirmed disconnect and expired-session gate. API responses were intercepted; this is not production login or worker evidence.
- [x] Targeted agent, bounded manual dispatch reconciliation, storage-check and CI workflows exist in `.github/workflows/`.
- [ ] Verify Neon schema **2** and runtime grants for `repository_setups`, then take a fresh encrypted backup. The saved Neon report establishes schema 1, not the current schema-2 rollout.
- [ ] Inspect the existing Render API account configuration: database region, deployed revision, runtime storage and server-only settings. Basic health and proxy boundaries passed; account configuration and worker readiness remain unverified.
- [ ] Inspect/provision the protected `torque-production` Actions environment and its secret/variable names; verify targeted worker execution and acceptance workflow access.
- [ ] Enable bounded dispatch reconciliation scheduling after provisioning and usage review. The existing reconciliation workflow is manual only.
- [ ] Complete real production OAuth/session, second-user isolation, repository onboarding, persisted run, cancellation, worker interruption, artifact retrieval/retention and explicit idempotent publication checks.
- [ ] Complete successful unseeded recovery, actual paid-provider graceful shutdown and actual publication/disconnect fencing trials within existing budgets.
- [ ] Confirm account quotas, off-machine encrypted backup custody, deployed logs/trace credential exclusion, billing and compatible rollback.

The initial share-link fetch was blocked by Vercel Authentication. A subsequent
authenticated CLI request reached Torque and returned `GitHub login required`.
This establishes signed-out frontend-to-API connectivity, not full OAuth acceptance.
Protection has not been disabled; cookies, state and redirect query values were
excluded from verification output.
Render and GitHub account reads are confirmed; Neon tools and GitHub environment
administration/dispatch remain unavailable in this session. Hosted worker
provisioning and credential-bearing trials cannot be marked complete.
See [current verification](evidence/deployment/current-verification.json).

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
- [x] Implement atomic admission and exclusive leases with a PostgreSQL transaction advisory lock; actual PostgreSQL concurrency verification is pending below.
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

- [ ] Current schema-2 PostgreSQL migration and runtime grants verified; saved schema-1 checks passed.
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
