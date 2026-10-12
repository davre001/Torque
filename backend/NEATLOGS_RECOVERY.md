# Neatlogs readback and recovery

## Acceptance diagnostics incident: October 12 instrumentation change

Incident `d5d9ddaa-09d9-4d5f-b73e-16128ecf6e3d` identified insufficient
per-test detail, not an established root cause for the underlying failed patches.
Independent suites now report each executed check by name, with actual duration,
bounded stdout/stderr, and a failure stack trace. The coordinating worker exports
these as child spans of the acceptance attempt, after subprocess completion.
`test.execution_duration_ms` is the execution duration; span wall time represents
reporting, not the original browser test duration. Known credentials are redacted.
Legacy results and infrastructure failures without case reports produce an
explicit runner-diagnostics child rather than invented individual test results.
The remote workflow uses unbuffered output, and the suites print named PASS/FAIL
records and bounded diagnostics. The reporting helper is mounted read-only and
included in the acceptance suite integrity digest.

Local verification: 59 targeted tests passed, including an actual failing
subprocess assertion, a passing rerun, child span parentage, stacktrace capture,
bounded output and credential redaction. Hosted verification passed on October 12:
failure trace `3d1061326c1185af4bec2113b7ebe57d` and passing trace
`b08c025e327bcaf698b4b1348e57a2e8`. MCP full-context readback verified the named
child check, captured stderr, and actual assertion stack trace. The SDK requires
canonical `neatlogs.tool.output` to preserve these diagnostics in hosted payloads;
arbitrary test attributes alone were absent from hosted readback. The Public API
returns span summaries; the probe uses MCP for full payload verification.
MCP reports successful spans as SUCCESS; the public summary reports OK.
Shipment of the remote workflow and browser suites remains pending. Do not mark
the incident resolved as a deployed fix based on this controlled probe alone.

After authorizing the upload of controlled test diagnostics, run this no-model,
no-GitHub probe to verify hosted attributes and export dashboard trace IDs:

```powershell
.\.venv\Scripts\python.exe -m backend.acceptance_telemetry_probe
```

Existing traces are immutable evidence: instrumentation applies to new runs.
No detection rate can be inferred from the reported invalid 1.7/1.8 rate values;
treat those metrics as unavailable.

The worker uses the SDK key only for ingestion at `https://ingest.neatlogs.com`.
An expiring `NEATLOGS_TOKEN` with `context:read` and `observability:read`, bound
to the project as Project Viewer, reads `https://app.neatlogs.com/api/v1/public`.
Keep both credentials in the ignored root `.env`; never put them in client code.

Each acceptance attempt has a separate completed workflow trace. Its name contains
the run ID and attempt number, and failed tests set its status to ERROR. This lets
recovery read a finalized attempt while the main issue workflow remains open.
The worker flushes before readback without shutting down the SDK between jobs.

Readback checks the exact ID, finalized status, ended spans, complete pagination,
span count, one matching root, parent references, and absence of cycles. It exports
only safe metadata and requires a failed span before supplying it to recovery.
The readback has bounded waits, requests, pages and response sizes. Revoked credentials,
missing traces or delayed finalization use an explicitly recorded local fallback.
Cancellation and budget checks remain active during polling. Prompts, source content
and exception payloads are masked; typed token counts remain numeric.

## Reproduce the controlled live drill

```powershell
.\.venv\Scripts\python.exe -m backend.recovery_demo
```

This uses the configured Gemini and Claude providers, at most six calls,
30,000 tokens, $0.50 estimated model cost and 240 seconds. It checks read access
before spending. It uses an isolated database under `var/recovery-demo/`, no GitHub
requests, and no production jobs or PRs. A deliberately incorrect first patch fails
an independent subprocess assertion. The model receives finalized hosted failure
metadata plus local assertion details, repairs the implementation, and the unchanged
test runs again. The reviewer must approve before evidence is exported.

Model-written code is parsed as AST and never executed. The drill is a small local
fixture, not proof of arbitrary repository support or natural autonomous failure.
If hosted readback falls back, the drill refuses to claim hosted recovery success.

## Verified evidence, October 11, 2026

- Original published kokon demo: finalized trace `65f1c230ec0f31c423c81d7f0e33ed02`,
  status OK, five spans. [Readback](../evidence/neatlogs/operator-demo-readback.json).
  This older trace has no LLM spans; its model usage is in the saved run artifacts.
- Controlled recovery: run `ce1d5d570a144e608d98d49031579dd2`, first attempt failed,
  second passed. Failed trace `e6417b8ff867e18db4fe1093548c91c2` finalized ERROR.
  Main trace `2b869453d595b5951eb2fd0fbb898021` finalized OK with 16 spans and four
  LLM calls. [Evidence](../evidence/recovery/ce1d5d570a144e608d98d49031579dd2/README.md).
- Provider accounting reports 3,484 tokens, including Gemini thinking tokens;
  Neatlogs reports 2,639 tokens. Do not treat these totals as identical. The Gemini
  requested alias is `gemini-3.5-flash`, while hosted spans report `gemini-3.6-flash`.
  These are recorded as observed, not silently normalized.
- Estimated model cost for the successful drill: $0.008778. Earlier failed drills
  remain in ignored `var/`; this figure is not the cumulative cost of all trials.

The original first-attempt kokon success still does not demonstrate recovery.
The controlled drill supplies separate evidence of actual hosted failure readback,
live recovery reasoning, a revised patch, and an independent passing assertion.
