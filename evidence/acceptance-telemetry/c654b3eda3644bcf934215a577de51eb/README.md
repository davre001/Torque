# Verified hosted acceptance diagnostics

Controlled probe run on October 12, 2026. No model calls, GitHub writes, or Docker
execution. It runs an independent subprocess AST assertion on a local fixture.

- Failed check: https://app.neatlogs.com/traces/3d1061326c1185af4bec2113b7ebe57d
- Passing check: https://app.neatlogs.com/traces/b08c025e327bcaf698b4b1348e57a2e8
- Incident: https://app.neatlogs.com/incidents?id=d5d9ddaa-09d9-4d5f-b73e-16128ecf6e3d

The failed attempt has an `acceptance-test-case` child span containing
`test.name=result-equals-10`, captured stderr, and the actual assertion stack trace:
`AssertionError: Expected result=10; actual=8`.
The fixture is then corrected to `result = 10`; the unchanged assertion passes.
This demonstrates the instrumentation fix, not a new autonomous agent recovery.

The full payload was verified using Neatlogs MCP `get_trace_context`; the Public
API summaries verified finalized traces and parentage. `failure.json` and
`passing.json` preserve sanitized diagnostics. The remote browser suites/workflow
have not been shipped by this probe; the incident was not marked resolved.

## Screen recording

1. Show the original incident's finding that individual test details are missing.
2. Open the failed trace above and select its `acceptance-test-case` child.
3. Show the tool output containing the check name, stderr, stacktrace, and actual
   execution duration. Span wall time is reporting time, not test execution time.
4. Open the passing trace and show the successful child check.
5. Explain: "Neatlogs identified a gap in our test observability. We added per-test
   diagnostics and verified that a forced failure now exposes its exact assertion.
   The same check passes when the controlled fixture is corrected."

Earlier unsuccessful readback probes in sibling folders are retained. They must
not be presented as fully verified instrumentation evidence.
