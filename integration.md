# Torque integration plan

Frontend API wiring is now implemented in `/workspace`: credentialed requests, CSRF,
persisted run polling/history, cancel, explicit publication, and confirmed disconnect.
The labeled landing preview remains separate. A live connected-user issue-to-PR run is saved under `evidence/github-app/`; disconnect/history acceptance remains pending.

Status: live operator/provider/browser/PR evidence, finalized trace readback, and controlled live hosted recovery are saved. Live connected-user execution and publication are verified in the saved Claude-only trial. Read current official SDK references during implementation; exact gateway model aliases and supported features must be discovered rather than guessed.

## Integration progress checklist

- [x] Prepare a pinned fork gallery profile and independently calibrate keyboard/alt/mouse browser assertions locally; see [gallery evidence](backend/GALLERY_VERIFICATION.md).
- [x] Deploy the gallery-capable workflow and verify its hosted baseline (Actions `38183797125`, three expected assertions fail, mouse regression passes).
- [x] Complete the fresh fork gallery issue: verified connected-user run published PR #5, now merged; see `evidence/gallery/completed-publication.json`.

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
- [x] Add worker-owned Neatlogs lifecycle/client wrappers and content masking; finalized workflow readbacks are saved. Dashboard screenshots remain pending.
- [x] Verify LiteLLM model access and usage reporting in the live run; total remaining credit balance is not independently audited.
- [x] Verify historical Gemini access and bounded errors/retries/token limits; later full investigation requests on 3.5/3.6 returned 503. The current verified workflow uses Claude-only mode.
- [x] Implement shared provider adapters, role routing, timeouts, and spending accounting.
- [x] Initialize worker Neatlogs once and verify finalized workflow/acceptance span trees through authenticated readback.
- [x] Obtain separate authorized neatlogs read credentials and implement failure-trace retrieval.
- [x] Verify finalized application traces and hosted recovery in an explicitly seeded controlled live drill; live repository recovery remains pending.
- [x] Verify GitHub source/destination identities and token permissions; select the demo fork.
- [x] Implement issue fetching, authenticated branch writes, and idempotent verified PR publication.
- [ ] Verify authorization separately before any upstream public contribution.
- [x] Implement supported Entire search/code context and save actual target-repository runtime evidence in the live slider trial.
- [x] Review shared hook/settings files and commit appropriate configuration without local state.
- [x] Use real workspace API polling, saved events, recovery/failure states, acceptance results, and actual PR links; landing preview remains labeled simulation.
- [x] Verify a live connected-user browser run with source installation access and a supported recipe; run `b220ce7e5cda4e14963c74fc04ad8711`, PR #3.
- [x] Show installed repository eligibility and reject browser submissions without an enabled source and reviewed test recipe before queueing.
- [x] Check configured credentials and decrypted App user token are absent from exported successful user-run evidence.
- [ ] Complete the broader credential audit across responses, sandbox environments, Git history, traces, and artifacts.
- [ ] Replace financial cost assumptions with measured run data when available.

Scope update: Connect GitHub leads to the authenticated workspace and confirmed disconnect. GitHub App identity/installation onboarding is implemented and verified in the controlled trial. The personal-token path remains for local operator development. Additional repository support and Entire Graph/Brain Continuous Memory remain optional later work.

- [x] Configure GitHub App user authorization and repository installations for the controlled connected-user flow.
- [x] Implement connect/callback/session/disconnect endpoints, secure sessions, and per-user repository/run ownership checks.
- [x] Implement publication/disconnect fencing and revocation checks; mocked tests pass.
- [ ] Verify live browser disconnect and publication fencing with real credentials.
- [x] Verify browser history persistence after refresh and reconnection; user confirmed PR #3 remains.
- [ ] Add public queue/spending controls and complete deployment acceptance.
- [ ] Verify recovery on a live GitHub repository; the existing hosted recovery drill is controlled and seeded.

## Configuration and provider routing

Load the root `.env` with `python-dotenv` before creating SDK clients. Environment variables already supplied by deployment take precedence. Validate required configuration without printing values; maintain `.env.example` with empty keys. API keys remain in the coordinator, never in Next.js client code, sandbox environment, Git URLs, trace attributes, or exported artifacts.

| Variable | Purpose |
| --- | --- |
| `NEATLOGS_API_KEY` | Existing project SDK ingest key |
| `LITELLM_API_KEY` | Hackathon gateway credential |
| `LITELLM_BASE_URL` | Actual organiser-provided API base URL |
| `LITELLM_MODEL` | Exact gateway alias for the selected Claude model |
| `GEMINI_API_KEY` | Google AI Studio credential |
| `GEMINI_MODEL` | Saved as `gemini-3.6-flash`; inactive in Claude-only mode; full investigation requests returned 503 |
| `TORQUE_PROVIDER_MODE` | Current `claude-only`; `mixed` restores Gemini investigation/review and Claude edits |
| `GITHUB_TOKEN` | Local operator's repository-scoped credential |

Database/workspace paths, source allowlist, publication destination, retry/model/token/dollar limits, test recipes, runner settings, and development origins are defined in `.env.example` and backend configuration.

Current verified mode is `TORQUE_PROVIDER_MODE=claude-only`: investigation, implementation, recovery, and review all use the existing Claude/LiteLLM connection and Claude cost rates. The optional `mixed` mode uses Gemini for investigation/review and Claude for edits/recovery. Test results remain authoritative regardless of model choice. Do not silently switch provider when quotas fail; persist the error and apply only a configured fallback within the same budget.

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

The workspace uses `POST /api/runs` and persisted polling; the landing preview remains labeled simulation. Handle queued, recovering, failed, cancelled, interrupted, ready-to-publish, and completed states explicitly; stop polling terminal states. Display only real PR URLs and trace references. Keep API credentials in Python and expose sanitized configuration readiness only.

## Integration acceptance

Check actual gateway and Gemini model access with small operator-authorized calls; verify token permissions on the selected destination without unsolicited writes. Then verify a real instrumented run, trace readback, Entire context evidence, controlled branch/PR publication, repeated publication idempotency, and absence of credentials in git, artifacts, API responses, and traces. Quota/auth failures must produce honest terminal or pending states, never simulated success.

## Controlled PR publication implementation

- [x] Explicit operator-authenticated API and CLI publication, exact verified content checks, and stale-base rejection.
- [x] Operator-owned source/fork permission checks, stable branch, draft PR, and SQLite publication lease.
- [x] Mocked GitHub tests cover retry after a lost PR response, branch conflicts, changed artifacts, and concurrent publication.
- [x] Live controlled-fork draft PR published and saved: [davre001/kokon #1](https://github.com/davre001/kokon/pull/1).
- [x] GitHub App authentication and publication for the controlled connected-user trial; broader users/repositories remain unverified.

Publication runs as a bounded explicit API/CLI operation; the agent pipeline remains in the separate SQLite-backed worker. See [publication instructions](backend/PUBLICATION.md). The operator and one controlled connected-user flow are live-verified; broader multi-user/public-deployment acceptance remains pending.

## Next work in order

1. Browser history/disconnect/reconnection is user-verified. Finish live publication/disconnect fencing acceptance.
2. Retention, local restart/API-restart/cancellation, remote cancellation, Windows Ctrl+Break, and live provider hard interruption are verified. Finish Linux signals and blocked-provider graceful shutdown before public deployment; see [scope and evidence](backend/LIFECYCLE_VERIFICATION.md).
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

- [x] Controlled live publication crash/reconciliation: PR #6 recovered after process kill with one PR-creation POST. Isolated database and clock-advanced lease expiry; deterministic fixture review, no model calls. See [scope and report](backend/LIFECYCLE_VERIFICATION.md).

## Admission limits implementation

API and CLI submissions now enforce atomic SQLite admission limits: total active
queue, per-user active runs, daily run count, and user/deployment daily dollar
reservations. Each admission reserves the full TORQUE_MAX_COST_USD cap. Failed or
cancelled runs retain reservations until the next UTC day; idempotent retries do
not reserve twice. Existing historical runs have no retrospective reservation.
These limits cover model estimates, not Actions/storage billing or HTTP login
rate limits. Single shared SQLite deployment only; public deployment acceptance
and broader credential audit remain pending. Entire runtime search currently
requires operator CLI login; no target context or live recovery is claimed yet.

Entire runtime adapter is implemented and disabled by default (`TORQUE_ENTIRE_CONTEXT=1` opts in).
It searches only the named target repository, saves sanitized result references, and
labels historical context separately from the pinned source revision. CLI login was
verified against Torque; the demo fork is not mirrored, so target-context and live
repository recovery acceptance remain unchecked.

## Entire target context readback verified

The user mirrored davre001/kokon in the EU region. Authenticated historical
search returned no results; actual Entire code search returned Gallery.tsx.
The runtime adapter now falls back to bounded code search, accepts only the
requested repository and reviewed context files, and checks each returned line
against local source before including it. Sanitized live adapter evidence is
saved in `evidence/entire-runtime/target-context.json`. Its reviewed local
fixture contains the previously documented harmless crash-test comment; this
is adapter readback, not a new complete agent run or runtime checkpoint.
Live repository recovery and broader credential/deployment acceptance remain pending.

Slider issue #7: dedicated reviewed profile and workflow deployed at `6b26912`;
hosted original-source baseline reproduced four assertions and passed one
regression group. The recipe is `backend/recipes.slider.json`, separate from
the completed gallery profile. No live agent or recovery attempt has run yet.

Live slider run `98557585701043f6b452f161b8dd0f96` retrieved runtime Entire
context and attempted genuine recovery twice. The second recovery fetched its
actual failed Neatlogs trace. All three attempts failed independent verification
(4/5, 4/5, 1/5), so successful live repository recovery remains unchecked. No PR
was created. Exported evidence and diagnosis are in evidence/slider/98557585701043f6b452f161b8dd0f96/.
The prompt now explains that recovery retries must rebuild the whole fix from
pinned originals; that change awaits a fresh live trial.

Recovery diagnostics update (October 12, 2026): the slider suite now reports
key sequence, previous value, expected value, and actual value without changing
its five acceptance groups. The actual failed patch reproduced:
`Home -> ArrowLeft; before=0; expected split=0; actual split=45`.
The labelled calibration fixture still passes 5/5. Recovery receives bounded
complete replacement strings and instructions distinguishing test-group counts
from failing assertion indices. Sanitized diagnostics are emitted on the Neatlogs
acceptance span as `torque.acceptance_diagnostics`; finalized trace identity and
local diagnostics remain separate evidence sources. A new hosted trial is pending
publication of the updated suite. Successful live recovery remains unchecked.

## Credential and deployment audit — October 12, 2026

- [x] Current credential exact-value exclusion audit: 384 files, 160 stored response records, 733 Git blobs and one encrypted user credential checked; no matches. Report: `evidence/security/credential-audit.json`.
- [x] Atomic admission controls implemented and tested; daily reservations remain enforced after cancellation/failure.
- [ ] Unknown/rotated credential scanning and external trace/dashboard/host-log review.
- [ ] Public host/browser acceptance, edge request limits, Linux shutdown checks and second-user deployment verification.

The read-only audit is repeatable with `python -m backend.security_audit`.
[Deployment readiness](backend/DEPLOYMENT_READINESS.md) records scope and limits.
These results do not mark live recovery or public deployment complete.
