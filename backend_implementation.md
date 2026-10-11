# Torque backend implementation plan

Status: design draft, October 11, 2026. This document describes planned behavior, not implemented capabilities. Related plans: [worker](background_worker.md), [integrations](integration.md). The existing root `implementation.md` remains the historical frontend plan.

## Implementation progress checklist

Mark functionality complete only after its relevant acceptance checks pass. Files containing docstrings alone remain pending.

- [x] Create core modules and agent/tool package placeholders.
- [x] Identify kokon issue #4 as the first demo candidate.
- [x] Add runtime/development dependency manifests, installed-environment lock, and installation instructions.
- [ ] Load root configuration, preserve deployment overrides, and validate execution limits.
- [ ] Implement typed run, attempt, plan, verification, and error records.
- [x] Implement SQLite storage, events, idempotent submissions, and transactional state updates.
- [x] Replace the legacy `suture` import and FastAPI background-task execution with queue submission.
- [ ] Implement submit, status, cancel, publish, and readiness endpoints; add SSE only if needed.
- [ ] Validate issue URLs, run IDs, caller ownership, and configured repository destinations.
- [ ] Prepare a pinned checkout and capture baseline test results.
- [ ] Implement bounded file access, structured patch validation, and credential-free sandbox tests.
- [ ] Implement Investigator context gathering and acceptance criteria.
- [ ] Implement model-generated edits through restricted tools.
- [ ] Implement Verifier with required tests as a hard publication gate.
- [ ] Implement trace-informed Recovery and distinct retry/budget counters.
- [ ] Persist verified patch/head records and enforce authorized publication.
- [ ] Reproduce the kokon bug and automate all three playback acceptance criteria.
- [ ] Test invalid paths, budgets, failures, cancellation, restart interruption, and duplicate publication.
- [ ] Wire Next.js to real statuses/results and document actual runnable commands.
- [ ] Verify the end-to-end run and export actual traces, tests, PR, and recovery evidence.

## Outcome and scope

Implemented milestone: configuration, state enums/validated submission records, SQLite queue and history,
authenticated local-operator API, separate worker, and read-only issue lookup.
See [backend/README.md](backend/README.md) for actual commands. Provider execution, visitor auth,
isolated tests, and publication remain pending. JSON event polling is implemented; SSE is pending.

Scope update: `changes.md` now specifies a public landing page and a separate authenticated workspace. Real Connect GitHub and Disconnect behavior require GitHub App identity/installation onboarding, server-side sessions, and per-user ownership checks in the current requested scope. The local single-operator path below remains the first development milestone; it does not fulfill multi-user connection behavior by itself.

- [ ] Add authenticated GitHub connect/callback/session/disconnect endpoints and authorized workspace access.
- [ ] Associate queued runs and publish permissions with the connected user and installation.
- [ ] Make disconnect request cancellation and block new writes under the disconnected credentials.

Accept a GitHub issue URL, inspect a pinned repository revision, implement a focused patch in an isolated checkout, run real tests, recover from failures using trace evidence, and produce a verified pull request or an explicit failure with supporting artifacts.

The hackathon release supports one local operator and one active run. Public multi-user hosting, GitHub App onboarding, broad language support, and automatic issue webhooks follow later. Public issue input is supported only when its source and destination repositories are configured for the operator; possession of a public issue URL does not grant write access.

First candidate: https://github.com/GabrieleLozupone/kokon/issues/4. Reproduce the reduced-motion video autoplay bug at a recorded commit before treating it as the demonstration case. Verify paused autoplay with reduced motion, manual playback, and unchanged ordinary playback. Use a controlled fork/test destination initially; publishing a PR to an external maintainer requires a separately authorized publish action.

## Existing state and proposed structure

`frontend/app.py` contains FastAPI run routes, JSON state files, and a deferred legacy import of an absent `suture` package. The Next.js UI currently simulates the agent. Keep the route contract, replace the task stub and legacy import with the `backend` package, and connect the UI to real run records. Torque remains the product name.

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
7. Save the verified patch and exact head SHA as `ready_to_publish`. Publish only according to the authorized destination policy, then record the actual PR URL and mark `completed`.

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
