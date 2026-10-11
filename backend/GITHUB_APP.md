# GitHub App login setup

The backend now supports GitHub App OAuth login, server-side encrypted user tokens,
opaque expiring sessions, installation repository discovery, per-user run ownership,
and CSRF-protected writes. Local operator bearer authentication remains available.

## Register and configure

Create a GitHub App at https://github.com/settings/apps/new.
For localhost development, configure:

- Homepage: `http://localhost:3000`
- User authorization callback: `http://localhost:8000/api/auth/github/callback`
- Repository permissions: Contents **read/write**, Issues **read**, Pull requests **read/write**; Metadata read is automatic.
- Enable expiring user access tokens. Sessions expire with the token (at most eight hours); reconnect instead of automatic refresh.
- Webhook: `/api/auth/github/webhook` on your publicly reachable HTTPS backend; set a webhook secret. The authorization-revoked event invalidates local credentials and sessions.
- Install the app on the repositories you want Torque to access. Login alone does not install it.

Populate the root `.env` fields from `.env.example`: `GITHUB_APP_ID`,
`GITHUB_APP_CLIENT_ID`, `GITHUB_APP_CLIENT_SECRET`, `GITHUB_APP_CALLBACK_URL`,
`GITHUB_APP_WEBHOOK_SECRET`, `TORQUE_FRONTEND_ORIGIN`, and `TORQUE_SESSION_ENCRYPTION_KEY`.
Generate the encryption key once:

```powershell
.\.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Keep the key and App secret private and stable across API/worker restarts. Use HTTPS
outside localhost; secure deployments use host-only `__Host-` cookies. Use the same
hostname consistently in development (do not mix localhost and 127.0.0.1). Keep the
frontend and API on the same site; CORS permits only the configured frontend origin.
Run production behind a proxy that redacts OAuth callback query strings from logs.

## Browser contract

- Navigate to `GET /api/auth/github/connect` to start login. Callback redirects to `/workspace`, which now loads your session, repositories, real runs, history, publication, and disconnect.
- `GET /api/auth/session` returns GitHub username, stable user ID, and a CSRF token; never provider credentials.
- `GET /api/auth/github/repositories` lists public repositories accessible to both the user and this App's installations.
- Browser requests include credentials; every POST includes `Origin` matching the configured frontend and `X-CSRF-Token` from the session endpoint.
- Existing run submit/status/history/events/cancel/publish routes enforce the current user's ownership. Other users' run IDs return 404.
- `POST /api/runs/{id}/publish?destination=user/repository` checks source installation access and destination write permissions using the user's encrypted App token, never the operator PAT. Current controlled-publication policy requires a user-owned source or fork and unchanged verified base SHA; organization-owned publication is not supported yet.
- `POST /api/auth/disconnect` revokes all local sessions/credentials and requests cancellation of unfinished runs. It returns 409 if publication is already in progress so remote writes can be reconciled first. This disconnects Torque locally; users can separately revoke App authorization in GitHub settings.

OAuth uses one-time, browser-bound state and S256 PKCE. SQLite stores only session
hashes and encrypted provider tokens. Installation checks are refreshed before submit,
execution and publication; provider revocation errors fail closed. Disconnect is
checked at worker boundaries; it cannot undo an already accepted external request.

The reviewed source allowlist and acceptance recipes still apply: login does not
enable arbitrary repositories or private source archives. Global provider credits and
the shared Actions runner remain operator resources; public hosting still needs rate,
queue and spending controls. No live App login is claimed until registration and a
browser trial are complete.

Reference: [GitHub App user authorization](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app).

## Frontend workspace

Run `npm run dev` from the repository root and open `http://localhost:3000/workspace`.
Landing-page Connect GitHub buttons start real login. Its labeled preview remains a
simulation; workspace progress comes from persisted backend records.

For another API address, copy `frontend/ui/.env.example` to `frontend/ui/.env.local`,
set `NEXT_PUBLIC_TORQUE_API_URL`, and restart Next.js. Match the backend frontend
origin and App callback hostname. This public setting contains only the API address.

Keep the separate worker running to execute queued jobs. Source installation access
and reviewed recipes remain required; installing the App on your fork does not grant
access to the upstream source repository. Live browser acceptance remains pending.
