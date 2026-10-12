# Live worker restart and cancellation verification

The isolated local drill uses actual Python worker processes, a real localhost API,
and a separate SQLite database. Its processor deliberately performs fixture work;
it does not call models, GitHub, or execute repository code.

```powershell
.\.venv\Scripts\python.exe -m backend.lifecycle_probe
```

Saved [local results](../evidence/lifecycle/ebe2cff1ed6c43ab8366999cd54b1579/report.json):

- Hard kills during investigation, implementation, verification, and recovery were
  followed by a worker restart after lease expiry. Each run became interrupted,
  executed once, was not replayed, and rejected the stale owner's heartbeat.
- Cancelling a queued job through the HTTP API prevented execution.
- A running job renewed its lease while the API process was killed and restarted.
  The restarted API read its persisted verifying state.
- Cancelling that running job through the restarted API stopped the worker
  cooperatively and persisted cancelled status.
- Calling `Worker.stop()` from a fixture trigger produced an interrupted outcome.
  This last check does not test delivery of an operating-system shutdown signal.

The separate remote drill dispatches one reviewed public kokon test job and cancels
it while in progress using the real `ActionsRunner` cancellation path:

```powershell
.\.venv\Scripts\python.exe -m backend.lifecycle_probe --remote
```

It requires the existing cached reviewed workspace and Actions configuration.
Saved [remote results](../evidence/lifecycle/95cecd4f46a5427ea5f34436633402b0/report.json)
confirm [Actions run 38177020201](https://github.com/davre001/Torque/actions/runs/38177020201)
completed with conclusion `cancelled`. No model calls or PR writes occurred.

These drills do not modify the production database.

## Provider interruption and Windows shutdown signal

The [updated local results](../evidence/lifecycle/30fa9e79dc554517b94c9e2642808bf2/report.json)
include a real Windows Ctrl+Break event delivered through
`GenerateConsoleCtrlEvent` to a hidden worker console. The worker exited with code
0 and persisted `interrupted`. The CLI now handles `SIGBREAK` as well as SIGINT and
SIGTERM. This checks fixture work with real OS delivery; Linux SIGINT/SIGTERM and
graceful shutdown while a provider is blocked are still separate pending checks.
The probe also supports SIGINT/SIGTERM when run on Linux.

```powershell
.\.venv\Scripts\python.exe -m backend.provider_interruption_probe
```

The [provider interruption result](../evidence/lifecycle/9a09a2319dcf435abeef1d9eab7c1a44/report.json)
records one real Claude gateway request through the existing LiteLLM adapter.
The isolated worker was killed while the synchronous request was outstanding.
After lease expiry, restart marked the run interrupted with one execution and no
replay. A conservative $0.008484 reservation was saved before dispatch; this is
not measured billing. The SDK request hook proves dispatch started, not that the
gateway accepted the request. No response was observed, and remote processing or
billing may continue after the client is killed. This small probe uses a maximum
$0.02 reservation and 128 output tokens, with no retry or production DB writes.
Its reservation is saved by the probe; this does not establish durable production
budget accounting across crashes or remote provider cancellation.

## Live publication crash trial

The controlled trial passed on October 12, 2026. See the
[report](../evidence/publication-crash/56cfbe0c39e140c6b4f4838f64a8206f/report.json)
and [draft PR #6](https://github.com/davre001/kokon/pull/6).
The publisher subprocess was killed after GitHub accepted PR creation and before
SQLite recorded completion. An immediate retry was fenced by the active lease.
After advancing only the isolated Store clock by 901 seconds, retry completed
using the same PR and head. Exactly one PR-creation POST occurred; a further
completed request also created nothing.

This used an isolated database, the current reviewed fork revision, and only a
non-executing comment. All four real gallery browser checks passed. Review was a
labelled deterministic fixture, with no model calls. It does not establish a fresh
agent fix or a real 15-minute wait. The production 900-second lease and completed
user run were unchanged. PR #6 remains draft and unmerged. Linux SIGINT/SIGTERM
and graceful shutdown during blocked provider calls remain pending.

Probe implementation: `backend/publication_crash_probe.py`. Each invocation makes
a new isolated fixture and draft PR; inspect existing evidence before rerunning.

## Unseeded slider recovery candidate

Fork [issue #7](https://github.com/davre001/kokon/issues/7) is open and unresolved
at reviewed SHA `218143b523252ee95c2368adc83fef95b324b156`. The independent
slider suite reproduced four failing browser groups with one regression group
passing; a labelled temporary positive calibration fixture passed all five.
See `evidence/slider/acceptance-validation.json`. Profile, compressed two-file
transport, immutable source gate, workflow capability check, and a dedicated
`backend/recipes.slider.json` policy are implemented. Deployment and hosted
baseline are still pending. No agent attempt or live recovery has run.

The positive fixture is only test calibration and must never seed the live run.
A naturally failed attempt followed by real hosted-evidence-driven correction
is required for the live recovery milestone. A first-attempt success counts as
a fix alone. PR publication is a separate explicit operation.
