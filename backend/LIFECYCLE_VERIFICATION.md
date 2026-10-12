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
baseline are verified. Failed live agent/recovery attempts are recorded below.

The positive fixture is only test calibration and must never seed the live run.
A naturally failed attempt followed by real hosted-evidence-driven correction
is required for the live recovery milestone. A first-attempt success counts as
a fix alone. PR publication is a separate explicit operation.

Hosted slider baseline (October 12, 2026):
[Actions run 38212472888](https://github.com/davre001/Torque/actions/runs/38212472888)
executed workflow revision `6b26912902db05536aa07cf48db7f22b236ff3df`.
Four assertion groups failed as expected; pointer/tab/media-call regression
passed. No infrastructure failure, model calls, PR writes, or production queue
changes occurred. Readback saved in
`evidence/slider/hosted-baseline-d1da7fd975584b798953fa9e4b161613.json`.

## Live slider trial setup failures

Run `c8f542337c71495f97de6028383ac9c0` stopped at the 16 KB
investigation context guard, with zero model calls. Reviewed excerpts were
narrowed to 9,406 bytes without changing source or acceptance criteria.
Run `6de4f02f375e44a297cc09e387f8d3c1` stopped at the patch
footprint guard after two genuine Claude calls (~$0.11445 estimated). The two
source files total 63,104 bytes; the guard counts both old and new bytes.
A process-only 150,000-byte cap is used for the next trial. The default
100,000-byte cap, file/hash checks, model spending limits, and suite remain intact.
Both outcomes are configuration/guard failures, not live test-driven recovery.
Their sanitized records and baseline/context artifacts are saved under evidence/slider/.

Run `9e664ae55b434decbb1f8da7abb2cf7c` stopped before implementation
at the existing conservative prompt-token reservation guard after one model
call (~$0.023286 estimated). Implementation previously received both complete
files; it now receives the same operator-reviewed excerpts as investigation.
Full-file SHA and exact unique replacement validation remain authoritative.
The 150,000-token/$2 run limits were not raised. This is not agent recovery.

## Genuine live recovery attempt ? not successful

Run `98557585701043f6b452f161b8dd0f96` failed after all three attempts.
Attempt results were 4/5, 4/5, 1/5 assertions. Recovery 2 retrieved the actual
failed Neatlogs attempt trace, while recovery 1 fell back to local artifacts.
Runtime Entire target context was available. Both bounded recovery retries
were exhausted; no PR was created. Evidence, hashes, and diagnosis are saved
in `evidence/slider/98557585701043f6b452f161b8dd0f96/`.
The failed final patch omitted previously successful changes after reset to
pinned originals. Implementation instructions now explicitly require a complete
solution each retry. Later run `2aa4615e4cbf48deadd99a009b8da11b` retained
the full fix but failed keyboard boundaries in all three attempts (4/5 each).
Improved diagnostics and actual replacement context are pushed; a fresh live
recovery trial remains blocked by daily admission limits.

## Graceful shutdown during blocked localhost provider I/O

The real Windows SIGBREAK probe saved
`evidence/lifecycle/806317a39ff24eee8028548b8edf5cef/report.json`.
A synchronous HTTP request was outstanding against a deliberately nonresponding
localhost fixture. OS signal delivery requested worker shutdown; after the fixture
adapter's two-second timeout, the worker exited with code 0 and persisted
`interrupted`. Exactly one uncertain reservation was retained and no transport
retry occurred. No model calls, PR writes or production database changes occurred.

The provider error path now checks shutdown/cancellation before retrying or marking
the run failed. This is real blocked HTTP I/O with a fixture provider, not evidence
of graceful termination during a real paid provider request. Production waits for
the adapter timeout (LiteLLM 45 seconds, Gemini 120 seconds); client interruption
does not establish server-side provider cancellation or billing cancellation.

Credential-free Linux verification is prepared in
`.github/workflows/torque-lifecycle-checks.yml`. It runs actual SIGINT/SIGTERM
lifecycle checks and SIGTERM during blocked local HTTP I/O, using isolated databases.
Hosted execution remains pending until its reports are inspected.
