# Torque development changes

Updated October 13, 2026. This replaces the earlier frontend suggestions with implemented milestones and explicit remaining acceptance work. Results below come from repository source and saved evidence; no new live run was performed for this update.

## October 13: current reviewed task

Commit `b6bff472404af9daf670b362b8cebb94b9fb7164` switches the default fork recipe from the completed gallery task to **slider-keyboard** for issue #7.

- Approved additional source revision: `513883a43ea33474431c933018b6267d08acb8f5`, alongside original slider pin `218143b523252ee95c2368adc83fef95b324b156`.
- The newer source changes only a Gallery comment; slider HTML/CSS are unchanged. Other revisions remain rejected.
- Editable paths are `site/index.html` and `site/assets/style.css`; all five independent acceptance groups remain required.
- The current-revision Edge baseline passed 1/5 groups and reproduced four assertion failures. Pointer/selection/media regressions passed. This is baseline evidence, not a successful repair.

[Acceptance setup and review](tests/acceptance/slider/README.md) ? [Recipe](backend/recipes.remote.json) ? [Source/profile guards](backend/acceptance_profiles.py)

## README and checkpoint publication

The README now explains the problem, solution, agent roles, workflow, architecture, safety boundaries, setup, sponsor integrations, verified results and remaining work. It includes Mermaid workflow/integration diagrams and evidence links.

Published commit: [4317988](https://github.com/davre001/Torque/commit/43179880579ef3d646b33fe38b5dee00c8cf9574). Entire-generated checkpoint: `01M4SE2FKCRGJ39A5YBTS0HE5K`; both commit and checkpoint ref were verified on origin. This was a README-only commit, not a runtime deployment verification.

## Frontend and GitHub access

- Replaced the historical simulated runner contract with a real session-aware `/workspace`, persisted progress/history, cancellation, test/review results, explicit publication and confirmed disconnect.
- Landing login entry starts GitHub OAuth; the illustrative preview remains separate.
- Repository access shows readiness labels. Setup controls were removed in `5420168` and readiness labels restored in `9db5057`; schema-2 backend setup storage remains implemented.
- Same-origin proxy checks cover cookies, redirects, origins, request sizes and server-only credential isolation.

[Frontend implementation](implementation.md) ? [Connected-user verification](evidence/github-app/README.md)

## Backend, worker and cloud preparation

- Implemented FastAPI authentication/ownership, encrypted GitHub credentials, durable queue/events/history, reviewed source/edits, independent acceptance and explicit publication.
- Added SQLite local storage and optional PostgreSQL, schema-2 repository setups, shared admission/leases, private durable artifacts and cloud publication from stored verified context.
- Added targeted Actions workers, stable dispatch IDs and bounded manual reconciliation. The reconciliation workflow has no automatic schedule.
- Recorded user-provided schema-2 restricted-role/grant confirmation. A fresh schema-2 encrypted backup and full hosted worker acceptance remain pending.
- Vercel frontend and Render API passed basic saved deployment checks. Last inspected runtime revision was `e582fb9`; subsequent Git commits do not establish deployment acceptance.

[Backend progress](backend.md) ? [Worker](background_worker.md) ? [Deployment](deployment.md)

## Agent results and sponsor integrations

- Reduced-motion operator/connected-user runs produced verified controlled-fork PRs; connected-user PR #3 is recorded as merged.
- Normal gallery execution published verified PR #5, recorded as merged. The separate publication-crash fixture is not an additional gallery fix.
- A controlled seeded failure was repaired after finalized Neatlogs readback and passed the unchanged assertion.
- Unseeded slider trials exhausted three attempts without publishing; successful unseeded recovery remains unverified.
- Per-check Neatlogs child spans now preserve names, bounded stdout/stderr and assertion stacks in canonical hosted diagnostic payloads.
- Entire captures development checkpoints and provides opt-in repository-scoped runtime search. Hosted worker context remains disabled until authenticated access is verified.
- cfo.ai financial evidence includes pricing, retry/success sensitivity, cash-flow forecasts, workbook/screenshots and selected measured model-cost samples.

[Gallery publication](evidence/gallery/completed-publication.json) ? [Recovery drill](evidence/recovery/ce1d5d570a144e608d98d49031579dd2/README.md) ? [Slider failure](evidence/slider/2aa4615e4cbf48deadd99a009b8da11b/README.md) ? [Integration status](integration.md)

## Verification and remaining gates

The last saved broad verification reports 192 Python tests passed, five skipped, TypeScript/proxy checks, production frontend build and Edge workspace fixtures. Lifecycle evidence covers actual Windows/Linux signals and blocked localhost provider I/O; paid-provider graceful shutdown remains separate.

Outstanding: full production login/worker/artifact/publication flow, second-user isolation, successful unseeded recovery, paid-provider shutdown, publication/disconnect fencing, fresh schema-2 backup, deployed retention/restore/rollback, credential/log exclusion, quotas and billing review.

This documentation refresh changes only Markdown. It does not provision accounts, execute jobs, inspect credentials, or verify a new deployment.
