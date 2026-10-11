# Torque integration plan

Status: draft. Credentials are locally configured but provider access and runtime instrumentation still need verification. Read current official SDK references during implementation; exact gateway model aliases and supported features must be discovered rather than guessed.

## Integration progress checklist

User-reported credential entry is setup progress, not proof of provider access. Synthetic SDK diagnostics are separate from application verification.

- [x] Create a key-free `.env.example` and ignore the local `.env`.
- [x] Record user-confirmed entry of Claude/LiteLLM, Gemini, and GitHub credentials.
- [x] Install Python neatlogs SDK locally and pass local Doctor validation.
- [x] Record the synthetic Doctor trace appearing in the dashboard; hosted readback initially timed out.
- [x] Enable/approve Entire development hooks and capture checkpoint evidence.
- [x] Commit cfo.ai financial model, screenshots, and assumptions summary.
- [x] Implement read-only issue fetching with strict GitHub URL parsing and mocked API tests.
- [x] Implement both provider SDK adapters and structured role routing; live access remains unchecked.
- [x] Implement explicit estimated budgets, bounded transport retries, and usage-required responses (zero rates only for verified free quota).
- [x] Add worker-owned Neatlogs lifecycle/client wrappers and content masking; dashboard acceptance remains unchecked.
- [ ] Verify the actual LiteLLM URL, model alias, permissions, usage reporting, and quota.
- [ ] Verify Gemini access to the configured model and handle its rate/quota limits.
- [ ] Implement shared provider adapters, role routing, timeouts, and spending accounting.
- [ ] Initialize neatlogs once per process and instrument each actual model/tool call without duplicates.
- [ ] Obtain separate authorized neatlogs read credentials and implement failure-trace retrieval.
- [ ] Verify finalized application traces and genuine trace-driven recovery.
- [ ] Verify GitHub source/destination identities and token permissions; select the demo fork.
- [ ] Implement issue fetching, authenticated branch writes, and idempotent verified PR publication.
- [ ] Verify authorization separately before any upstream public contribution.
- [ ] Implement a supported Entire context adapter and save actual target-repository context evidence.
- [ ] Review shared hook/settings files and commit appropriate configuration without local state.
- [ ] Replace frontend simulation with real API polling and handle all planned statuses.
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
| `GEMINI_MODEL` | User-selected `gemini-3.8-flash`; confirm account access before relying on it |
| `GITHUB_TOKEN` | Local operator's repository-scoped credential |

Additional proposed settings: database/workspace locations, allowed source/destination repositories, max recovery retries (2), model/token/dollar limits, test recipe, and API development origins. Add them to the example when implementation defines the actual names.

Route implementation and recovery to Claude through LiteLLM; route investigation summaries and verification reasoning to Gemini. First establish a Claude-only execution path, then add Gemini. Test results remain authoritative regardless of model choice. Do not silently switch provider when quotas fail; persist the error and apply only a configured fallback within the same budget.

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

The cfo.ai spreadsheet, screenshots, and summary are committed under `business/`; there is no runtime cfo.ai API integration. After real runs, use measured tokens, retry rates, sandbox duration, and successful PR rate to revise financial assumptions. Keep the documented narrative/spreadsheet discrepancy visible until corrected.

Replace Next.js simulation events with `POST /api/runs` and persisted polling. Handle queued, recovering, failed, cancelled, interrupted, ready-to-publish, and completed states explicitly; stop polling terminal states. Display only real PR URLs and trace references. Keep API credentials in Python and expose sanitized configuration readiness only.

## Integration acceptance

Check actual gateway and Gemini model access with small operator-authorized calls; verify token permissions on the selected destination without unsolicited writes. Then verify a real instrumented run, trace readback, Entire context evidence, controlled branch/PR publication, repeated publication idempotency, and absence of credentials in git, artifacts, API responses, and traces. Quota/auth failures must produce honest terminal or pending states, never simulated success.

## Controlled PR publication implementation

- [x] Explicit operator-authenticated API and CLI publication, exact verified content checks, and stale-base rejection.
- [x] Operator-owned source/fork permission checks, stable branch, draft PR, and SQLite publication lease.
- [x] Mocked GitHub tests cover retry after a lost PR response, branch conflicts, changed artifacts, and concurrent publication.
- [ ] Live publication to a configured controlled fork and recording its PR URL as demo evidence.
- [ ] GitHub App authentication and publication for connected visitors.

Publication runs as a bounded explicit API/CLI operation; the agent pipeline remains in the separate SQLite-backed worker. See [publication instructions](backend/PUBLICATION.md). Earlier pending-publication checklist entries now refer to live validation and the public multi-user flow.
