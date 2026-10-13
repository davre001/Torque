# Torque backend implementation plan

## Database verification update — October 13, 2026

User-provided Neon SQL results confirm schema version 2 and runtime role
`torque_runtime_4833357e53e3` with all four elevated role flags disabled,
SELECT/INSERT/UPDATE/DELETE on all 15 Torque tables (including repository_setups),
no CREATE on public schema, and USAGE on the events sequence. These are user-reported
checks, not an independent agent query. Fresh schema-2 encrypted backup and
production worker/end-to-end verification remain pending.


## Current implementation and acceptance — October 12, 2026

Connected-account update: the Render deployment matches `e582fb9`, with automatic
`main` deployments in Oregon. GitHub CI run `38296501216` passed. None of the 47
repository workflow runs is an agent-worker run. The deployed service has no
configured health-check path; set `/health` on the existing service. Neon schema
verification and Actions secret provisioning/dispatch still need account tools
not currently exposed here.

Current local checks passed: **192 Python tests, 5 skipped**, TypeScript, proxy
contracts and production Next.js build. Python tests disabled dotenv loading;
no `.env` inspection or credential-bearing live trial was performed. Historical
counts and proposed structures below are retained as design history.

The implemented API is `backend.api:app`; Next.js lives in `frontend/ui` and is
already wired to persisted run/session/repository endpoints. Execution stays in a
separate worker. Storage supports SQLite locally and PostgreSQL in cloud mode;
the current migration version is **2** for per-user repository setups. Targeted
Actions execution, dispatch reconciliation and private database artifacts exist.

The frontend is deployed at https://torque-pied.vercel.app (`e582fb9`, READY),
with automatic deployments from `main`. This does not complete production API,
worker or full OAuth acceptance. Render API https://torque-sxqr.onrender.com
returned health 200/ok. Authenticated CLI probing reached the signed-out session
route, OAuth entry redirected to GitHub and untrusted direct OAuth returned 403.
These establish basic API connectivity and boundaries, not a completed login/run.

Still required: verify schema-2 migration and restricted grants; inspect/provision
Render and protected Actions settings; complete production browser and second-user
checks, hosted onboarding and issue-to-PR run, artifact persistence/retention,
cancellation/reconciliation and rollback. Successful unseeded recovery,
paid-provider graceful shutdown and live publication/disconnect fencing remain
separate evidence gates. Automatic GitHub token refresh is not implemented.
See [deployment status](deployment.md) and
[current verification](evidence/deployment/current-verification.json).

Workspace milestone: real session-based `/workspace` and landing OAuth buttons are
implemented. User runs are polled from the API; the controlled connected-user run and publication are verified.

Status: implementation and verification progress, October 12, 2026. Checklists distinguish tested code from
pending live acceptance. Related plans: [worker](background_worker.md), [integrations](integration.md).
The existing root `implementation.md` remains the historical frontend plan.

## Implementation progress checklist

Mark functionality complete only after its relevant acceptance checks pass. Files containing docstrings alone remain pending.

- [x] Create core modules and agent/tool package placeholders.
- [x] Identify kokon issue #4 as the first demo candidate.
- [x] Add runtime/development dependency manifests, installed-environment lock, and installation instructions.
- [x] Load root configuration, preserve deployment overrides, and validate execution limits.
- [x] Add repeatable read-only current credential exclusion audit and atomic admission limits.
- [x] Audit selected finalized live Neatlogs payloads and verify hosted Linux lifecycle/blocked-localhost I/O shutdown.
- [ ] Complete host-log/unknown-credential review, actual paid-provider graceful shutdown and public-host acceptance; see [deployment readiness](backend/DEPLOYMENT_READINESS.md).
- [x] Implement typed submission, plan, patch, review, recovery, and test records; attempts persist structured JSON.
- [x] Implement SQLite storage, events, idempotent submissions, and transactional state updates.
- [x] Replace the legacy `suture` import and FastAPI background-task execution with queue submission.
- [x] Implement submit, status, history, cancel, publish, readiness, and JSON event-polling endpoints; SSE is optional.
- [x] Validate issue URLs, run IDs, caller ownership, and configured repository destinations.
- [x] Prepare a pinned checkout and capture baseline test results.
- [x] Implement bounded file access, structured patch validation, and credential-free sandbox tests.
- [x] Implement Investigator with bounded context and immutable operator criteria (fixture-tested).
- [x] Implement structured model edits through allowlisted, source-hash-checked file tools.
- [x] Implement Verifier with required tests as a hard gate (fixture-tested and live demo passed).
- [x] Implement local-artifact Recovery and distinct transport/recovery budget counters.
- [x] Implement authorized hosted-trace-informed Recovery; verified in a controlled live drill with a seeded failure.
- [x] Persist verified patch/head records and enforce authorized publication.
- [x] Reproduce the kokon bug and automate all three playback acceptance criteria.
- [x] Test invalid paths, budgets, failures, cancellation, restart interruption, and duplicate publication.
- [x] Wire Next.js to real statuses/results and document actual runnable commands.
- [x] Verify connected-user execution and publication against an installed supported source repository; saved PR #3/#5 evidence.
- [x] Expose repository eligibility and prevent unsupported connected-user submissions from entering the queue.
- [x] Verify the live operator issue-to-PR flow and export actual tests, usage, patch, and PR evidence.
- [x] Export finalized application trace and controlled live hosted recovery evidence; natural GitHub-repository recovery remains pending.

## Outcome and scope

Implemented: configuration, typed records, SQLite queue/history/events, operator-authenticated
API, separate worker, pinned source snapshots, restricted edits, provider budgets, remote
Linux browser tests, local-artifact recovery, and explicit controlled-fork draft PR publication.

Live demo run `6634790aa28943629348e02914d9b56c` reproduced the baseline bug, passed
all three independent browser criteria after the first patch, and published
[davre001/kokon #1](https://github.com/davre001/kokon/pull/1). Saved
[evidence](evidence/runs/6634790aa28943629348e02914d9b56c/README.md) records source,
verified content, published commit, model usage, and original artifacts. Current automated validation: 192 passed, five skipped (October 12, 2026).

Recovery uses authenticated finalized failure traces alongside local artifacts and passed a controlled seeded drill. Runtime Entire context and connected-user execution are verified. Unseeded slider attempts have not recovered successfully. See `backend/NEATLOGS_RECOVERY.md` and `backend/LIFECYCLE_VERIFICATION.md` for evidence and limits.

Scope update: `changes.md` now specifies a public landing page and a separate authenticated workspace. Real Connect GitHub and Disconnect behavior require GitHub App identity/installation onboarding, server-side sessions, and per-user ownership checks in the current requested scope. The local single-operator path below remains the first development milestone; it does not fulfill multi-user connection behavior by itself.

- [x] Add authenticated GitHub connect/callback/session/disconnect endpoints and authorized workspace access.
- [x] Associate queued runs and publish permissions with the connected user and installation.
- [x] Make disconnect request cancellation and block new writes under disconnected credentials; actual in-flight publication/disconnect acceptance remains separate.

Accept a GitHub issue URL, inspect a pinned repository revision, implement a focused patch in an isolated checkout, run real tests, recover from failures using trace evidence, and produce a verified pull request or an explicit failure with supporting artifacts.

The controlled release supports local operator access and GitHub App connected users, with one executing worker job at a time and per-user admission/ownership controls. One connected-user flow is live verified. Public hosting acceptance, broad repository support and automatic issue webhooks remain separate later work. Repositories need an installation, deployment allowlist and reviewed test recipe; a public issue URL does not grant write access.

First candidate: https://github.com/GabrieleLozupone/kokon/issues/4. Reproduce the reduced-motion video autoplay bug at a recorded commit before treating it as the demonstration case. Verify paused autoplay with reduced motion, manual playback, and unchanged ordinary playback. Use a controlled fork/test destination initially; publishing a PR to an external maintainer requires a separately authorized publish action.

## Existing state and proposed structure

The implemented entry point is `backend.api:app`; the Next.js UI is connected to
persisted backend run records. The following proposed layout is historical and
must not be used as deployment instructions. Torque remains the product name.

```text
backend/                   # Python package; design documents are at root
  __main__.py              # CLI, worker, preflight commands
  config.py                # root .env loading and validated limits
  models.py                # typed run, attempt, plan, verification records
  store.py                 # SQLite queue and state transactions
  orchestrator.py          # bounded state machine, shared by CLI and worker
  worker.py                # claims, leases, cancellation, shutdown
  agents/                  # investigator, implementer, verifier, recovery
  integrations/            # provider, GitHub, neatlogs, Entire adapters
  tools/                   # bounded file access, patching, sandbox tests
frontend/app.py            # FastAPI transport, enqueue and status queries
tests/                     # orchestration, API, tools, worker tests
var/                       # ignored database, checkouts, raw run artifacts
evidence/runs/             # selected sanitized submission evidence
```

Add a Python dependency manifest and installation instructions during implementation. Use Python 3.11, FastAPI/Pydantic, SQLite, provider SDKs, neatlogs, and pytest. No orchestration framework is required: four agent roles can share one explicit coordinator and restricted tools.

## API and frontend contract

| Route | Planned behavior |
| --- | --- |
| `POST /api/runs` | Validate issue URL and preflight, persist queued job, return 201 with `run_id` and `status`; no model execution in the handler |
| `GET /api/runs/{run_id}` | Return persisted state, attempts, plan summary, test summaries, trace/checkpoint references, PR URL, and sanitized errors |
| `GET /api/runs/{run_id}/events` | Optional SSE using monotonically increasing stored event IDs; polling is the first implementation |
| `POST /api/runs/{run_id}/cancel` | Persist cancellation request; worker stops at safe boundaries and terminates active subprocesses |
| `POST /api/runs/{run_id}/publish` | Publish an already verified patch to the approved destination; reject stale or failed verification |
| `GET /health` | Report process readiness and local configuration presence without credentials |

Accept only HTTPS `github.com/<owner>/<repo>/issues/<positive-number>` paths; construct API requests from parsed identifiers. Validate run IDs before storage lookup. Return 422 for invalid input, 404 for unknown run, and 409 for incompatible publish/cancel requests. Use an idempotency key for repeated submissions; reusing a key with different input returns 409.

Preserve `queued`, `investigating`, `implementing`, `verifying`, `recovering`, `completed`, and `failed`; add `ready_to_publish`, `publishing`, `cancelled`, and `interrupted`. Update the frontend type and rendering together. `completed` requires a recorded PR URL; an unpublished verified patch is `ready_to_publish`.

Bind the prototype to localhost. Configure exact development origins for CORS or use a Next.js proxy. Public deployment requires caller authentication, per-user ownership checks, rate limits, and isolated execution before accepting arbitrary user work.

## Run records and execution

Persist issue URL, source owner/repo/base SHA, destination repo/base branch, branch name, status, current agent, timestamps, budgets, cancellation flag, model identities, trace IDs, checkpoint references, and PR URL. Attempts record their number, strategy, patch hash, test command/exit code, assertion results, failure category, usage, and trace IDs. Never persist keys in these records.

1. Resolve the issue, repository defaults, permissions, and immutable base SHA. Check that the source issue remains relevant.
2. Create a dedicated checkout and branch under `var/workspaces/<run_id>`. Read repository instructions as scoped project guidance; issue text and retrieved files are untrusted data and cannot grant new tool privileges.
3. Investigator gathers bounded source context with Entire where supported, establishes acceptance criteria, identifies tests, and returns a structured plan. Record baseline test results before edits.
4. Implementer proposes structured file edits. Validate paths, patch size, and permitted files before applying changes. No unrestricted model-generated shell commands.
5. Execute the configured test suite in the execution sandbox. Verifier checks the patch, all issue criteria, and actual test output. A model's verdict cannot override a failed required test.
6. If eligible, Recovery reads the failed trace and artifacts, changes the hypothesis or patch, and triggers another implementation/verification attempt.
7. Save verified content and patch digests as `ready_to_publish`; GitHub head SHA is recorded during explicit publication. Publish only according to the authorized destination policy, then record the actual PR URL and mark `completed`.

Default: one initial attempt plus at most two recovery retries (three total attempts), matching the business model. Track provider/network retries separately with their own bounds. Set explicit total wall time, model-call count, output-token, patch-size, test timeout, and dollar limits in configuration. The financial model's $1.65 is an estimate, not a proven runtime cap. Stop when a hard limit is reached; uncertain usage must not silently expand the budget.

Verification criteria are defined before patch generation. Keep regression tests outside agent-editable paths or audit edits to them, so an agent cannot pass by weakening assertions. Do not deliberately make bad patches for the demo: use genuine recorded failures or a clearly labeled reproducible test fixture.

## Execution isolation

A Git worktree separates files but does not sandbox code. Run dependency installation and repository tests in a container or equivalent restricted runner without provider/GitHub credentials, with time, CPU, memory, process, output, and network limits. The coordinator owns authenticated API calls and publishing. Keep file tools inside the resolved checkout, reject traversal and escaping symlinks, and constrain commands to a configured repository test recipe.

If an isolated runner is unavailable, restrict the prototype to an explicitly trusted fixture and report that limitation. Do not present it as safe public execution of arbitrary repositories.

## Build sequence and completion checks

1. Configuration and preflight: load saved keys privately; validate actual model access and GitHub permissions with opt-in small probes.
2. Storage, queue, worker, API: submit/poll/cancel real persisted jobs before adding models.
3. Investigator and sandbox baseline: fetch the selected issue and revision; reproduce the bug with independent assertions.
4. Implementer and Verifier: complete one real patch/test cycle and save a verified artifact.
5. Recovery and telemetry: demonstrate bounded adaptation from a real failure; persist trace and test evidence.
6. Publishing and UI: publish to the controlled destination, show its PR in Next.js, and document the operator commands.

Required tests cover URL/path rejection, state transitions, duplicate jobs, lease ownership, retries and budgets, patch rejection, test failure blocking publication, cancellation, restart interruption, provider errors, trace unavailability, and idempotent PR creation. The end-to-end browser case must exercise all three reduced-motion criteria rather than inspect only HTML strings.

Before demo: verify an actual finalized neatlogs trace, inspect Entire context/checkpoints, link the cfo.ai plan, capture a genuine failure/recovery comparison, and replace README commands that reference nonexistent files. Keep raw runs ignored and export only selected sanitized evidence.

## Controlled PR publication implementation

- [x] Explicit operator-authenticated API and CLI publication, exact verified content checks, and stale-base rejection.
- [x] Operator-owned source/fork permission checks, stable branch, draft PR, and SQLite publication lease.
- [x] Mocked GitHub tests cover retry after a lost PR response, branch conflicts, changed artifacts, and concurrent publication.
- [x] Live controlled-fork draft PR published and saved: [davre001/kokon #1](https://github.com/davre001/kokon/pull/1).
- [x] GitHub App authentication and controlled connected-user publication; broader public-host acceptance remains separate.

Publication runs as a bounded explicit API/CLI operation; the agent pipeline remains in the separate SQLite-backed worker. See [publication instructions](backend/PUBLICATION.md). The operator and controlled connected-user flows are live-verified; acceptance on an actual public multi-user deployment remains pending.

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
- [x] Register/configure the actual GitHub App and complete live browser-login and installed-repository acceptance.
- [x] Wire landing-page connection and workspace UI to these backend endpoints.

The earlier unchecked GitHub App items now refer to live acceptance and frontend integration. Backend code is implemented; [GitHub App setup](backend/GITHUB_APP.md) records the required settings and current limitations. Expired sessions require reconnection; automatic token refresh is not implemented. The reviewed public-source allowlist/recipes and controlled user-owned publication policy still apply.
