# Backend tests

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
