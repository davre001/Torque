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

## Audit procedure

Run `.\.venv\Scripts\python.exe -m backend.security_audit` from the repository root.
It reads current configured credentials and decryptable stored GitHub user tokens
in memory, then checks tracked files, local artifacts/evidence, persisted run,
attempt and event response data, and blobs reachable from valid local Git refs
and HEAD. The report contains locations and counts only, never matched values.
Output: `evidence/security/credential-audit.json`.

This is an exact-value exclusion check. It cannot rule out unknown/rotated secrets,
remote-only Git objects or leaks in external dashboards and host access logs.
Broken local refs are explicitly excluded. Identity/session/CSRF fields legitimately
returned to the authenticated owner are not treated as application credentials.

## Defaults and limits

The queue accepts at most 20 active jobs, one active job per user, five admissions
per user per UTC day, $10 reserved per user per UTC day and $20 per deployment.
Each admission reserves the full per-run cap ($2 by default), even after failure
or cancellation. These reservations are conservative accounting, not actual bills.
The API and worker must share one SQLite database and consistent configuration.
These limits do not cover Actions/storage bills or authenticated read traffic.

## Public release remains blocked on

- [ ] HTTPS deployment with exact production callback/frontend origins and secure cookies verified in a real browser.
- [ ] Secrets provisioned server-side; restricted database/private-file access and backups verified on the host.
- [ ] Edge request/body/rate limits, including login, webhook, polling and publication endpoints; trusted host/proxy configuration.
- [ ] Operator bearer access isolated from public traffic; public health output reviewed for operational disclosure.
- [ ] Linux SIGINT/SIGTERM and graceful cancellation during blocked provider calls verified.
- [ ] External trace/export and deployment-log credential review, including unknown/rotated credential scanning.
- [ ] Second-user isolation and shared-database admission behavior verified on the actual deployment.
- [ ] Restore/retention and rollback procedure exercised on the production host.

Arbitrary repositories and horizontally scaled independent SQLite databases remain
unsupported. Keep recovery acceptance separate: a failed live attempt must be
repaired and pass every criterion before claiming genuine live recovery.
