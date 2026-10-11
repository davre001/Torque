# Backend tests

## Hosted recovery

`test_neatlogs_read.py`, `test_hosted_recovery.py`, `test_telemetry_mask.py`, and
`test_gemini_schema.py` verify credential separation, bounded response/pagination,
exact finalized trace identity, hierarchy, safe metadata, failure-only recovery,
labeled local fallback, detached attempt traces with restored workflow context,
typed usage preservation, and native Gemini schema submission.

The live drill is separate from these fixtures: see
[saved controlled recovery evidence](../evidence/recovery/ce1d5d570a144e608d98d49031579dd2/README.md)
and [setup/limits](../backend/NEATLOGS_RECOVERY.md). It deliberately seeds the first
incorrect patch and does not submit jobs to GitHub or the production database.

## Workspace browser contract

With Next.js running, use `node tests/workspace-browser.mjs` (Node 22+ and Microsoft
Edge on Windows). Set `TORQUE_TEST_BROWSER` to another Chromium executable if needed.
The headless test intercepts API requests with explicit fixtures: session/CSRF,
submission, recovery, acceptance results, terminal polling, PR results, saved failures,
disconnect confirmation, and expired login. It makes no live jobs or GitHub writes.
This verifies UI behavior; live connected-user execution is a separate acceptance step.

Tests will be added as behavior is implemented. Planned coverage: API contracts, job claims and leases, restart interruption, cancellation, retry budgets, file/patch boundaries, provider failures, trace readback, and idempotent publication. Use independent browser assertions for the kokon reduced-motion issue.
Run the backend foundation tests from the repository root:

```powershell
.venv/Scripts/python.exe -m pytest -q
```

`test_backend.py` covers durable submissions/history, competing worker claims,
lease expiry/renewal, cancellation, redacted failures, authenticated API routes,
and mocked GitHub reads. It does not verify live model calls, sandboxed repository
tests, visitor login, or PR publication.

`test_pipeline.py` adds deterministic failure/recovery fixtures, test-gate enforcement,
budgets, immutable source/patch validation, artifacts, and telemetry masking.
The independent browser script under `tests/acceptance` is excluded from ordinary
pytest collection and must run inside its reviewed Docker image.
# Repository eligibility

`python -m pytest tests/test_repository_policy.py tests/test_github_auth.py tests/test_backend.py -q`
checks that a browser caller needs both an enabled repository and a reviewed recipe;
unsupported submissions create no queued jobs. The workspace browser fixture also
checks unavailable-repository explanations, disabled submission, and refreshed access.
These checks do not prove a live GitHub App user run or worker availability.
