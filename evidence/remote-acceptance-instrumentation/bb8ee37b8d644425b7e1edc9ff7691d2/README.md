# Remote acceptance instrumentation verification

PR: https://github.com/davre001/Torque/pull/1

Verified branch: `fix/acceptance-test-diagnostics`.
Both remote runs used commit `ce4d43c0c25a25e53610ca6ee5b340c27f87042b`.
Pinned source revision: `995b078b79819c0049db3eef96fc6bd91b016b12`.
Both used identical acceptance-suite digest
`23cc4a51df0dc735ff300852aac18c44334a96bd5ee3e8c5a768e91b9941f5c0`.

- Baseline: https://github.com/davre001/Torque/actions/runs/38259846032
  Original reduced-motion source reproduced an assertion failure. The remote
  result includes a named failed check and an actual assertion stack trace.
- Fixed: https://github.com/davre001/Torque/actions/runs/38260001074
  Applying the existing saved verified patch passed all three browser checks.

The coordinator workflow jobs finish successfully when they upload valid result
artifacts; test success/failure is recorded inside those artifacts. Baseline job
success does not mean the baseline assertions passed.

No models were called. Browser-derived diagnostic results were saved locally and
were not uploaded to Neatlogs. Separate fixture probes established canonical
Neatlogs diagnostic payload readback. This verifies the reduced-motion browser
profile; gallery and slider profiles were changed but not remotely exercised here.

The user merged PR #1 into `main` on October 12 at
`ad0cf740f8f9166d33ce625618eec31c4ccbfbac`. Read-only GitHub tree comparison
confirmed that all 15 instrumentation files match the verified PR commit.
Unrelated staged deployment changes were excluded. The Neatlogs incident was
marked resolved with a note documenting the verification scope and limits.
