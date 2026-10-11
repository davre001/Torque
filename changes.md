# Frontend pages and routes: suggested changes

Reviewed October 11, 2026 against `README.md`, `backend_implementation.md`, `background_worker.md`, and `integration.md`. This is a source review, not a browser-rendering or live endpoint verification. Suggestions below are not implemented.

## Accepted landing page and workspace requirements

These user requirements supersede earlier recommendations to keep the issue runner on `/` or postpone GitHub connection UI. They define the next frontend implementation; they are not yet implemented.

### Landing page: `/`

- [ ] Build distinct Hero, How it works, Getting started, Why Torque, Evidence/integrations, FAQ, and Footer sections. Keep explanations concrete and avoid claims of measured performance before real runs exist.
- [ ] Use larger headings and body text throughout, especially How it works. Suggested responsive sizes: hero heading 48–72px, section headings 32–48px, explanatory body 18–22px; scale for narrow screens without horizontal overflow.
- [ ] Replace the glass navigation with a solid, clean header: Torque logo at top left, Get started at top right. Keep it accessible on mobile. Get started launches the same GitHub connection flow as the hero CTA.
- [ ] Hero primary button: Connect GitHub with the official public GitHub mark. Secondary button: How it works, linking to the section. Replace landing-page Run Torque CTAs with Connect GitHub.
- [ ] Animate a decorative GitHub issue URL with typing/deleting, cycling roughly three examples. Identify these as examples, not supported fixes or completed work; use generic owner/repo examples where needed. Include the selected kokon issue as a candidate example only.
- [ ] Keep animation text separate from editable input; it must not submit changing URLs or read each character through a live region. Reduced motion shows one static example.
- [ ] How it works: large readable steps for Connect GitHub → Select repository and issue → Investigate/implement/test → Recover if needed → Review verified result/PR. Show recovery as conditional.
- [ ] Getting started: connect an account, authorize a repository, supply/select an issue, then run Torque in the workspace. State access requirements in plain language.
- [ ] Why Torque: explain test-gated changes, bounded recovery, and inspectable evidence. Evidence/integrations: explain neatlogs, Entire, and the cfo.ai business plan with genuine links when available.
- [ ] FAQ covers repository access, failed runs, publishing, and disconnect behavior. Footer includes product name, repository, relevant docs/evidence, and actual links only.
- [ ] Restore the normal browser cursor throughout. Remove any custom X/crosshair cursor while retaining standard pointer cursors on interactive controls.

### Connected workspace: `/workspace`

- [ ] Successful GitHub authentication redirects here; unauthenticated visitors are sent to connection flow or the landing page. A cancelled/failed connection displays an error, not a fake authenticated workspace.
- [ ] Header greets the actual connected account: “Hello, <GitHub username>” with a subtly animated waving emoji. Provide static motion fallback and accessible emoji text.
- [ ] Start with a clean empty state and Run Torque button. Include a repository/issue selector or input before execution: GitHub connection alone cannot determine which issue to fix. Validate a selected authorized destination.
- [ ] Clicking Run Torque with a valid selection enqueues a real job and displays its persisted progress. Prevent duplicate submissions and retain the active run across refresh.
- [ ] Show progress in an animated glassmorphism rounded rectangle on this page. Glass styling belongs to the workflow panel, not the landing navigation. Maintain sufficient contrast and a solid fallback.
- [ ] Animate transitions based on actual backend stages, not predetermined timers. Show attempts, required tests, recovery, trace references, verified patch, and real PR result; support failed, interrupted, cancelled, and ready-to-publish states.
- [ ] Include Disconnect GitHub in the workspace navigation. Clicking it opens a confirmation dialog with Cancel and Disconnect, keyboard support, focus return, and a clear consequence statement.
- [ ] Confirmed disconnect invalidates the Torque session and stored account connection and returns to `/`. Cancel leaves the session unchanged. If work is running, request cancellation and prevent new publishing; reconcile any external write already in flight. Do not claim that local disconnect automatically uninstalls the GitHub App or removes existing PRs.

### Authentication dependency and completion checks

- [ ] Implement real GitHub identity/session authentication and repository authorization. The shared prototype `GITHUB_TOKEN` cannot authenticate every visitor or establish ownership of their repositories.
- [ ] Configure a GitHub App and its user authorization/installation flow; use server-side credentials, OAuth state validation, secure HTTP-only sessions, and per-user access checks. Installation tokens operate only within granted access. Never send client secrets or tokens to browser storage.
- [ ] Add backend connect/callback/session/disconnect endpoints and the required private environment configuration after selecting the actual GitHub App flow. Record exact callback URLs for local development/deployment.
- [ ] Test connection success/cancellation, unavailable installations, unauthorized repository selection, protected workspace access, username rendering, disconnect confirm/cancel, and disconnect during a run.
- [ ] Test the landing/workspace on mobile and desktop with keyboard navigation and reduced motion. Verify all three example URLs cycle only when motion is enabled.

This raises authentication into the current requested scope. Until those endpoints and GitHub App credentials exist, a visual preview must be labeled as a preview and cannot claim that connecting GitHub worked.

## Assessment

The main screen fits Torque's goal: GitHub issue input, four agent roles, progress, attempt history, and a PR result. Torque branding and metadata are consistent with that purpose. However, the primary Next.js run flow is a timed simulation, navigation exposes component demonstrations, and the transport/state contract does not yet match the planned separate worker and SQLite backend. It is currently a UI prototype, not a working issue-to-PR interface.

Keep the existing visual direction, logo, issue form, agent explanations, attempt history, and result panel. Focus changes on truthful behavior, useful navigation, persistent run state, and verified evidence rather than a redesign.

## Current route inventory

| Surface | Current implementation | Alignment |
| --- | --- | --- |
| Next.js `/` | `frontend/ui/app/page.tsx`; app and component-demo views selected with React state | Main app fits the concept, but views are not separate URL routes |
| Next.js `/?demo=1` | Prefills the FastAPI issue; normal submit still invokes the same simulation | Does not distinguish a real run from a preview |
| Next.js `/api/*` | No route handlers or backend rewrite found; `next.config.ts` has no API proxy | Real run requests need an explicit connection to FastAPI |
| FastAPI `/` | `frontend/app.py` serves the legacy static frontend | Duplicates the Next.js product surface |
| FastAPI `POST /api/runs` | Saves JSON and starts `BackgroundTasks` with a legacy `suture` import | Must become SQLite queue submission for the separate worker |
| FastAPI `GET /api/runs/{run_id}` | Reads JSON run state | Contract is useful, storage must change |
| FastAPI `GET /api/runs/{run_id}/events` | Poll-style SSE with no event IDs | Optional; durable event IDs/reconnection are needed if retained |
| Cancel, publish, readiness | Planned but absent | Required for the chosen backend contract |

“Sonar Demo” and “Header Demo” are local component previews, not backend features or genuine run history. Only the root Next.js page was found; don't advertise unimplemented pages as working routes.

## Priority 0: make the main run flow real

- [ ] Replace the timer schedule in `frontend/ui/app/page.tsx:startRun` with API submission and polling of the returned run ID.
- [ ] Remove invented trace IDs, checkpoint IDs, test counts, progress logs, run ID `run_20261011_001`, and the hard-coded FastAPI PR URL from the real run path. Render only persisted backend values.
- [ ] Keep simulation only behind an explicit, visibly labeled “UI preview — no agent runs or PRs created” mode if it remains useful. Preview must not silently run when the backend fails.
- [ ] Remove the automatic fetch-failure-to-simulation fallback in `frontend/static/app.js` if that frontend is retained. Show a backend connection error instead.
- [ ] Connect Next.js to Python with a same-origin `/api` rewrite/proxy or a configured API origin and exact CORS policy. Do not implement a second orchestrator in Next.js. Configure readiness routing consistently if `/health` is proxied.
- [ ] Change FastAPI submission to persist a SQLite job; the separate worker claims it. HTTP handlers must not execute agents through `BackgroundTasks`.
- [ ] Show “backend unavailable,” “worker unavailable/queued,” and provider/auth configuration failures accurately. Browser failure to fetch status must not be presented as proof that the job failed.

Done when: submitting a real issue returns a persisted run ID, queued progress becomes actual worker progress, API/worker failures stay visible, and no invented success is displayed.

## Priority 1: match the run contract and lifecycle

- [ ] Add `ready_to_publish`, `publishing`, `cancelled`, and `interrupted` to frontend status types and renderers. Preserve failed and cancelled attempts rather than assuming every attempt passes eventually.
- [ ] Make attempt trace IDs and optional details nullable: queued/failed telemetry may have no ID yet. Standardize attempt status names; the legacy static frontend uses `done`, while Next.js uses `passed`.
- [ ] Render current attempt and maximum attempts from backend fields. Remove the literal “Recovery · Attempt 2 of 3” and fixed counters; distinguish initial attempt plus two recovery retries from three retries.
- [ ] Show separate “verifying,” “verified patch ready,” “publishing,” and “PR created” outcomes. `completed` requires an actual PR URL; passing tests alone must not claim a PR exists.
- [ ] Derive agent completion/skipped/failed indicators from recorded stage events. The current index/status comparisons and the fixed Recovery-before-Verifier ordering can imply recovery happened on a successful first attempt.
- [ ] Add a Cancel action backed by the cancel endpoint. Resetting the UI or selecting another preset must not pretend to cancel backend work.
- [ ] Add a Publish action for a verified patch when the selected policy requires operator authorization. Display source repository and destination fork/base branch before publication, so the user knows where the PR goes.
- [ ] Store or navigate to the returned run ID and restore status after page refresh. Avoid creating another job on status retry; preserve submission idempotency keys for ambiguous network outcomes.
- [ ] Stop polling on completed, failed, cancelled, and interrupted results; pause job-progress polling at `ready_to_publish`, while allowing refresh/publish actions. Resume polling after publication starts.
- [ ] Abort stale status requests, avoid overlapping polls, and clear requests/timers on unmount. Ignore a response belonging to a previously selected run. Existing simulation timers are cleared on reset but have no component-unmount cleanup.
- [ ] Allow a fresh submission after any terminal result. The current Next.js button remains disabled for `failed` and labels it as running unless the user resets manually.
- [ ] Disable preset changes while a submit is pending or provide an explicit switch-view action without deleting the active job's record.

Done when: refresh, retries, cancellation, publication, failed verification, and first-attempt success all produce truthful, recoverable UI states.

## Priority 1: useful navigation and demo input

Recommended minimal route map:

| Route | Purpose | Scope |
| --- | --- | --- |
| `/` | Issue entry and short explanation of Torque | Hackathon |
| `/runs/[run_id]` | Durable progress, attempts, test evidence, and final result | Hackathon; may initially be a root query parameter instead |
| `/preview` | Explicit simulated UI demonstration, if retained | Optional |
| `/runs` | Prior operator runs from persisted storage | Later unless needed for the demo |
| `/settings/connections` | User GitHub App/provider connection management | Public-product phase |

- [ ] Replace “App Interface,” “Sonar Demo,” and “Header Demo” product navigation with “Run Torque” and genuine run/evidence navigation. Keep component previews outside the primary user flow or behind development-only access.
- [ ] Use actual links for URL-addressable pages and working section anchors for explanatory content. Do not add dead History/Settings links before those pages exist.
- [ ] Fix the top “Run Torque” action to switch to the app before scrolling; its input ref isn't mounted while a component demo is visible.
- [ ] Remove or wire the Header demo's inert “Sign In” and “Get Started” buttons and `#features`, `#pipeline`, `#about` anchors. Do not imply account authentication exists in this local prototype.
- [ ] Replace the FastAPI/SQLAlchemy fixture presets and fabricated recovery descriptions with the selected kokon issue candidate, clearly marked “candidate” until baseline reproduction passes. Do not promise a specific failure/recovery path before it actually occurs.
- [ ] Make `?demo=1` prefill the selected issue only; distinguish that convenience from explicit preview simulation.
- [ ] Validate an exact GitHub issue path and positive issue number. `type="url"` alone accepts unrelated URLs; the legacy regex also accepts unwanted trailing paths. Show an inline, accessible error and retain the user's input. Server validation remains authoritative.

Done when: all visible navigation goes somewhere useful, normal run submission is unambiguous, and fixtures reflect the actual demo plan.

## Priority 1: evidence and result integrity

- [ ] Provide genuine clickable neatlogs trace URLs when available. Current Next.js attempts show trace text only; legacy links use `href="#"`. Keep pending IDs as plain text until an actual link is supplied.
- [ ] Show verification commands, exit results, acceptance-criterion outcomes, tested head SHA, and changed files alongside the PR. Label unavailable metrics instead of filling placeholders.
- [ ] Display actual Entire context/checkpoint references without claiming provider SDK calls automatically create coding-agent checkpoints.
- [ ] Distinguish live trace readback from local-artifact fallback during recovery. Keep synthetic Doctor traces separate from real application evidence.
- [ ] Validate backend-provided external URLs before rendering links, especially in the legacy HTML renderer. HTML escaping does not by itself reject unsafe URL schemes. Use approved HTTPS hosts and `rel="noopener noreferrer"` for new-tab links.
- [ ] Add a concise evidence link to the repository's real `evidence/` and `business/` documents for judges, if useful. cfo.ai belongs in supporting business evidence, not as a fictional runtime agent stage.

Done when: every success/test/recovery claim is backed by the matching recorded run and reviewers can inspect its artifacts.

## Priority 2: accessibility and maintainability

- [ ] Give the issue input a visible label and associate validation text with it. Add `aria-invalid` when appropriate.
- [ ] Give the mobile navigation toggle `aria-expanded` and `aria-controls`; handle Escape, keyboard focus, and return focus on close. Give icon-only reset/cancel controls explicit accessible names.
- [ ] Announce status changes with a polite live region and errors with an alert. Avoid announcing every log line or forcing scroll when a user is reading old output.
- [ ] Respect reduced motion across smooth scrolling, spinning/pulsing status indicators, and drawer transitions. Preserve the SonarGrid's existing media-query and event-listener cleanup rather than replacing it blindly.
- [ ] Extract the large page into issue form, navigation, status, attempts, result, and run-state hook modules. Share API types with a deliberate contract; don't spread backend field assumptions throughout JSX.
- [ ] Choose Next.js as the canonical product frontend. Retire the static frontend later or label it as a maintained fallback with the identical status/API contract. Update root README startup instructions to distinguish Next.js, API, and worker.
- [ ] Consolidate the duplicate header implementations after choosing the product navigation. Keep optional demos separated from application state.

## Completion and review checklist

- [x] Inspect source pages, component navigation, static client, Next.js config, and FastAPI routes.
- [x] Compare the UI with the separate-worker/SQLite plan and selected issue candidate.
- [ ] Implement Priority 0 API wiring after the backend endpoints exist.
- [ ] Implement Priority 1 run lifecycle, navigation, and evidence behavior.
- [ ] Verify real submission, refresh/resume, API outage, delayed worker, failed tests, recovery, cancellation, and authorized publish in a browser.
- [ ] Verify mobile and keyboard navigation, reduced motion, accessible errors, and valid external links.
- [ ] Confirm no simulated trace/test/PR values appear in the real run path.
- [ ] Run relevant frontend checks and contract tests after implementation.

No frontend code, routes, backend functionality, or dependencies were changed by this review.
