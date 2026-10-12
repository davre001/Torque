# Credential audit and public deployment gate

Torque remains a controlled prototype. The credential audit and admission controls
do not constitute public deployment acceptance.

## Implemented controls

- [x] GitHub App identity, encrypted server-side user credentials, expiring sessions, HTTPS cookies, exact-origin CORS and CSRF checks.
- [x] Per-user run ownership and repository authorization; visitor runs never substitute an operator PAT.
- [x] Operator-reviewed public repository revisions, editable files and immutable acceptance suites.
- [x] Docker tests without inherited application credentials, network access, writable source or elevated capabilities; CPU, memory, process and output limits.
- [x] Hosted test dispatch excludes provider/App credentials; checkout disables persisted Git credentials.
- [x] Structured outputs, artifact redaction, telemetry content masking and safe provider error messages.
- [x] Atomic SQLite queue/concurrency and daily count/dollar admission reservations, plus per-run call/token/dollar/time/retry caps.
- [x] Explicit verified publication with destination authorization and idempotent side-effect reconciliation.
- [x] Opt-in public mode enforces a callback host allowlist, bounded actual request bodies, shared SQLite per-IP/deployment request counters, disabled operator bearer access and minimal health output.

## Audit procedure

Run `.\.venv\Scripts\python.exe -m backend.security_audit` from the repository root.
It reads current configured credentials and decryptable stored GitHub user tokens
in memory, then checks tracked files, local artifacts/evidence, persisted run,
attempt and event response data, and blobs reachable from valid local Git refs
and HEAD. The report contains locations and counts only, never matched values.
Output: `evidence/security/credential-audit.json`.

This combines exact-value exclusion with recognizable GitHub, Google and Anthropic
token patterns and private-key PEM markers. It cannot rule out other unknown/rotated secrets,
remote-only Git objects or leaks in external dashboards and host access logs.
Broken local refs are explicitly excluded. Identity/session/CSRF fields legitimately
returned to the authenticated owner are not treated as application credentials.

## Defaults and limits

The queue accepts at most 20 active jobs, one active job per user, five admissions
per user per UTC day, $10 reserved per user per UTC day and $20 per deployment.
Each admission reserves the full per-run cap ($2 by default), even after failure
or cancellation. These reservations are conservative accounting, not actual bills.
The API and worker must share one SQLite database and consistent configuration.
These admission limits do not cover Actions/storage bills. Public HTTP counters
separately cover read, login, webhook and publication requests.

Set `TORQUE_PUBLIC_MODE=1` only on the production API, with an empty
`TORQUE_OPERATOR_TOKEN`, a configured GitHub App, HTTPS callback and frontend
origins. Startup rejects insecure or operator-enabled public configuration.
The default body cap is 65,536 bytes; default HTTP limits are 120 requests per
IP per minute and 600 per deployment per minute. Actual streamed bytes are checked,
not only Content-Length. Counters use the API's client address and the shared
SQLite database; configure the proxy's trusted addresses explicitly, never trust
arbitrary forwarded headers. Configure edge connection/read timeouts and limits
as well: an app-level body cap cannot stop a slow connection at the proxy.
Public mode remains off locally and does not alter daily model admission limits.
Keep frontend and API on HTTPS origins within the same site (for example,
`torque.example` and `api.torque.example`), or use a same-origin proxy.
The existing host-only session cookies use SameSite=Lax; unrelated frontend/API
sites will not support credentialed cross-site fetch with that cookie policy.

## Public release remains blocked on

- [ ] HTTPS deployment with exact production callback/frontend origins and secure cookies verified in a real browser.
- [ ] Secrets provisioned server-side; restricted database/private-file access and backups verified on the host.
- [x] Implement app-level body/rate/host limits covering login, webhook, polling and publication; verify with local tests.
- [ ] Verify edge connection/read limits and trusted proxy/host configuration on the deployed host.
- [x] Disable operator bearer access and expose minimal health output in public mode; local HTTP tests pass.
- [x] Hosted Linux SIGINT/SIGTERM and blocked localhost provider-fixture shutdown verified; Actions `38225586443`.
- [ ] Actual paid-provider graceful shutdown; fixture HTTP and earlier hard process kill do not establish this.
- [x] Scan common secret patterns alongside current credentials in valid local Git history and artifacts.
- [x] Read-only current-credential audit of three actual finalized Neatlogs traces (63 spans), without exporting raw payloads; `evidence/security/neatlogs-credential-audit.json`.
- [ ] Review deployment logs and unknown secrets outside recognizable patterns; no production backend host yet.
- [ ] Second-user isolation and shared-database admission behavior verified on the actual deployment.
- [ ] Restore/retention and rollback procedure exercised on the production host.

Arbitrary repositories and horizontally scaled independent SQLite databases remain
unsupported. Keep recovery acceptance separate: a failed live attempt must be
repaired and pass every criterion before claiming genuine live recovery.
