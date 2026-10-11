# Torque integration plan

Frontend API wiring is now implemented in `/workspace`: credentialed requests, CSRF,
persisted run polling/history, cancel, explicit publication, and confirmed disconnect.
The labeled landing preview remains separate. Connected-user browser acceptance is pending.

Status: implemented single-operator integrations with live provider/browser/PR evidence; hosted trace readback and public-user integration remain pending. Read current official SDK references during implementation; exact gateway model aliases and supported features must be discovered rather than guessed.

## Integration progress checklist

User-reported credential entry is setup progress, not proof of provider access. Synthetic SDK diagnostics are separate from application verification.

- [x] Create a key-free `.env.example` and ignore the local `.env`.
- [x] Record user-confirmed entry of Claude/LiteLLM, Gemini, and GitHub credentials.
- [x] Install Python neatlogs SDK locally and pass local Doctor validation.
- [x] Record the synthetic Doctor trace appearing in the dashboard; hosted readback initially timed out.
- [x] Enable/approve Entire development hooks and capture checkpoint evidence.
- [x] Commit cfo.ai financial model, screenshots, and assumptions summary.
- [x] Implement read-only issue fetching with strict GitHub URL parsing and mocked API tests.
- [x] Implement both provider SDK adapters and structured role routing; live access verified in the saved demo.
- [x] Implement explicit estimated budgets, bounded transport retries, and usage-required responses (zero rates only for verified free quota).
- [x] Add worker-owned Neatlogs lifecycle/client wrappers and content masking; dashboard acceptance remains unchecked.
- [x] Verify LiteLLM model access and usage reporting in the live run; total remaining credit balance is not independently audited.
- [x] Verify Gemini 3.5 Flash access; implement bounded provider errors/retries and token limits.
- [x] Implement shared provider adapters, role routing, timeouts, and spending accounting.
- [x] Initialize worker Neatlogs once and wrap model/tool calls; finalized dashboard span-tree acceptance remains pending.
- [ ] Obtain separate authorized neatlogs read credentials and implement failure-trace retrieval.
- [ ] Verify finalized application traces and genuine trace-driven recovery.
- [x] Verify GitHub source/destination identities and token permissions; select the demo fork.
- [x] Implement issue fetching, authenticated branch writes, and idempotent verified PR publication.
- [ ] Verify authorization separately before any upstream public contribution.
- [ ] Implement a supported Entire context adapter and save actual target-repository context evidence.
- [x] Review shared hook/settings files and commit appropriate configuration without local state.
- [x] Use real workspace API polling, saved events, recovery/failure states, acceptance results, and actual PR links; landing preview remains labeled simulation.
- [ ] Verify a live connected-user browser run with source installation access and a supported recipe.
- [ ] Verify secrets stay out of responses, sandbox environments, Git history, traces, and exported artifacts.
- [ ] Replace financial cost assumptions with measured run data when available.

Scope update: the requested landing-page Connect GitHub → authenticated workspace → confirmed disconnect flow makes GitHub App identity/installation onboarding part of the current frontend integration work. See `changes.md` for its acceptance checklist. The personal-token path remains useful for local backend development, but cannot substitute for authenticating visitors. Additional repository support and Entire Graph/Brain Continuous Memory remain optional later work.

- [ ] Configure GitHub App user authorization and repository installations for the requested connection flow.
- [ ] Implement connect/callback/session/disconnect endpoints, secure sessions, and per-user repository/run ownership checks.
- [ ] Prevent publication after disconnect and reconcile any write already in progress.

## Configuration and provider routing

Load the root `.env` with `python-dotenv` before creating SDK clients. Environment variables already supplied by deployment take precedence. Validate required configuration without printing values; maintain `.env.example` with empty keys. API keys remain in the coordinator, never in Next.js client code, sandbox environment, Git URLs, trace attributes, or exported artifacts.

| Variable | Purpose |
| --- | --- |
| `NEATLOGS_API_KEY` | Existing project SDK ingest key |
| `LITELLM_API_KEY` | Hackathon gateway credential |
| `LITELLM_BASE_URL` | Actual organiser-provided API base URL |
| `LITELLM_MODEL` | Exact gateway alias for the selected Claude model |
| `GEMINI_API_KEY` | Google AI Studio credential |
| `GEMINI_MODEL` | `gemini-3.5-flash`, verified in the saved demo; availability is account-dependent |
| `GITHUB_TOKEN` | Local operator's repository-scoped credential |

Database/workspace paths, source allowlist, publication destination, retry/model/token/dollar limits, test recipes, runner settings, and development origins are defined in `.env.example` and backend configuration.

Route implementation and recovery to Claude through LiteLLM; route investigation summaries and verification reasoning to Gemini. The implemented path uses Gemini for investigation/review and Claude for edits/recovery. Test results remain authoritative regardless of model choice. Do not silently switch provider when quotas fail; persist the error and apply only a configured fallback within the same budget.

If the gateway supports OpenAI-compatible chat completions, use a client configured with its explicit URL/key and model alias. This is distinct from calling Anthropic directly and does not require an invented Anthropic key. Confirm tool calling, structured response, usage accounting, and context limits for the actual gateway. Use Google's official `google-genai` SDK for direct Gemini access; its default endpoint handles routing without a custom Gemini URL.

The $20 gateway allocation is a shared budget assumption pending actual quota verification. Two provider credentials do not imply unlimited capacity. Record usage and selected models per attempt, distinguish actual reported cost from estimated cost, and enforce conservative limits when provider usage is unavailable.

## Neatlogs

Project ID: `00fd5eb9-0f63-473e-babc-4621191e4a4d`. Ingest base: `https://ingest.neatlogs.com`; dashboard/CLI host: `https://app.neatlogs.com`. These serve different purposes.

Initialize once per process, after environment loading. Name the root workflow `github-issue-to-pr`; add run/attempt identifiers as metadata. Capture model clients using the documented mechanism for the chosen library, once per call: wrap an OpenAI-compatible client for gateway calls and the Google GenAI client for direct Gemini calls when the current reference supports them. Do not attach duplicate auto-instrumentation and wrappers to the same calls.

Add meaningful spans for the issue workflow, agent roles, source lookup, patch application, tests, verification, and publication. Record failures before recovery reads them. Keep secrets and excessive repository content out of trace inputs/outputs. Finish spans and flush on one-shot process exit; long-running worker/API processes flush and shut down on process termination, not on every job.

SDK Doctor local/probe checks validate the SDK and a synthetic pipeline only. Acceptance requires the actual agent's finalized trace and its expected span tree, usage, failures, and retries. Existing Doctor trace `219851050b14a47507240e0e09bbaa15` is setup evidence, not an agent execution result.

Recovery's strong path queries its failed trace through an authorized neatlogs read adapter. The SDK ingest key must not be treated as a public API credential: obtain browser-approved CLI authentication or a securely provisioned service-account token with the needed read scopes. Use the explicit dashboard host/profile/project for CLI commands and confirm installed command syntax. Do not initiate interactive login from a background worker.

Persist local test logs and failure summaries even if hosted finalization is delayed. If recovery uses those local artifacts instead of a fetched trace, record that fallback honestly; do not claim dashboard-driven recovery. Require actual readback before calling the full trace-driven recovery milestone complete.

References: https://docs.neatlogs.com/sdk/python and https://docs.neatlogs.com/api-reference/authentication.

## GitHub and publication

Separate issue reading, checkout preparation, and publishing behind an authentication adapter so a GitHub App can replace the personal token later. Fetch issue metadata and repository defaults with timeouts/rate-limit handling. Pin the source SHA and persist both source and destination identities.

For a controlled repository owned by the operator, a fine-grained token needs selected-repository access, Contents read/write, Pull requests read/write, and Issues read. A token scoped to Torque does not automatically cover a separate demo repository or fork.

For the public kokon issue, create or select an operator-owned fork and verify permissions. Fine-grained tokens have limitations for contributing to public repositories outside the owner's memberships; verify upstream PR authorization before implementing that publish path. The first verified patch can be published as a PR within the controlled fork, clearly labeled as a demo referencing the source issue. An upstream contribution needs an appropriate GitHub App/user credential or supported token workflow and explicit authorization to publish there.

Never push to the source repository's default branch or merge a PR automatically. Push a stable run-specific branch, check for an existing PR by head/base, and create/reuse a draft PR only after deterministic verification. Include issue reference, base/head SHAs, change summary, executed tests, limitations, attempt summary, and actual trace/checkpoint references. Recheck changed source/base revisions before publication and reverify if the patch must be rebased.

Later public product: GitHub App installation access for approved repositories, per-user authorization, short-lived installation tokens, and an explicitly designed fork/upstream workflow. Installation access alone is not permission to write to every public repository.

## Entire

Entire hooks and captured development checkpoints are already enabled. Keep reviewed shared settings and hook files in version control; local auth, transcripts, caches, and machine-specific state stay private according to Entire's generated ignore rules.

Two uses must remain distinct: development checkpoints capture our coding work; runtime context helps Torque's Investigator understand the target checkout. Inspect `entire agent-help` and installed capabilities to choose supported search/Graph operations. Local file search can supplement context but cannot be labeled Entire output. Save command, checkout revision, query, and sanitized result references as evidence.

Running provider SDKs does not automatically create an Entire-compatible coding-agent session. Verify whether a supported session integration can capture runtime edits before claiming runtime checkpoint coverage. Existing development checkpoint evidence still demonstrates Entire use; add genuine runtime context evidence when available. Graph/Brain and Continuous Memory remain optional and are not prerequisites for the first backend path.

Do not let a run switch Entire repository settings, import unrelated sessions, or mutate the operator's auth. Avoid stale IDs or fabricated web links: record actual checkpoint IDs and verify judge-accessible links separately.

## cfo.ai and frontend

The cfo.ai spreadsheet, screenshots, and summary are committed under `cfo.ai/`; there is no runtime cfo.ai API integration. After real runs, use measured tokens, retry rates, sandbox duration, and successful PR rate to revise financial assumptions. Keep the documented narrative/spreadsheet discrepancy visible until corrected.

Replace Next.js simulation events with `POST /api/runs` and persisted polling. Handle queued, recovering, failed, cancelled, interrupted, ready-to-publish, and completed states explicitly; stop polling terminal states. Display only real PR URLs and trace references. Keep API credentials in Python and expose sanitized configuration readiness only.

## Integration acceptance

Check actual gateway and Gemini model access with small operator-authorized calls; verify token permissions on the selected destination without unsolicited writes. Then verify a real instrumented run, trace readback, Entire context evidence, controlled branch/PR publication, repeated publication idempotency, and absence of credentials in git, artifacts, API responses, and traces. Quota/auth failures must produce honest terminal or pending states, never simulated success.

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
