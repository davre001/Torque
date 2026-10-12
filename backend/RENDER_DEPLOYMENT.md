# Render API deployment

Prepared configuration: [`render.yaml`](../render.yaml). No Render service has
been created yet. The API uses Neon; the worker runs separately on GitHub Actions.

## Prerequisites

- [ ] Connect Render and grant access to `davre001/Torque`.
- [ ] Commit and push the reviewed cloud implementation and Render configuration.
- [ ] Confirm the Neon region; the Blueprint currently selects Frankfurt. Change
  it before creation if another supported Render region is closer to Neon.
- [ ] Obtain the stable Vercel production origin for GitHub login and the proxy.
- [ ] Provision the protected Actions worker environment before accepting runs.

## Create the service

Use Render **New → Web Service**, select `davre001/Torque`, branch `main`, and
leave **Root Directory empty**. Alternatively use **New → Blueprint** once the
configuration is pushed. Do not create a second service using both methods.

| Setting | Value |
| --- | --- |
| Name | `torque-api` |
| Runtime | Python 3, using root `.python-version` (3.11) |
| Plan | Free |
| Build | `pip install -r requirements.txt` |
| Start | `python -m uvicorn backend.api:app --host 0.0.0.0 --port $PORT --no-proxy-headers` |
| Health check | `/health` |
| Automatic deploys | Off during initial verification |

Set `PYTHON_VERSION=3.11.11` in Render's environment settings. It takes
precedence over `.python-version`. A Python 3.14 build cannot install the required
Neatlogs SDK (which requires Python >=3.10 and <3.14). If this error appears,
save the version setting and use **Manual Deploy → Clear build cache & deploy**.

Set the fixed values in `render.yaml` and supply its `sync: false` values through
Render's environment settings. Copy individual values from ignored local `.env`;
do not upload the entire file.

| Environment setting | Source |
| --- | --- |
| `TORQUE_DATABASE_URL` | Restricted Neon runtime URL, not the owner URL |
| `TORQUE_SESSION_ENCRYPTION_KEY` | Existing shared encryption key; same value in Actions |
| `TORQUE_ACTIONS_TOKEN` | Credential permitted to dispatch/read Torque workflows |
| `TORQUE_PROXY_SECRET` | Random shared server secret; identical in Vercel |
| `TORQUE_FRONTEND_ORIGIN` | Stable `https://<frontend-host>` |
| `TORQUE_BACKEND_ORIGIN` | Generated `https://<api-host>.onrender.com` |
| `GITHUB_APP_CALLBACK_URL` | Frontend origin + `/api/auth/github/callback` |
| `GITHUB_APP_ID`, `GITHUB_APP_CLIENT_ID`, `GITHUB_APP_CLIENT_SECRET` | Existing App configuration |
| `TORQUE_ALLOWED_REPOSITORIES` | Existing reviewed allowlist |

Do not provision `TORQUE_MIGRATION_DATABASE_URL`, `DATABASE_URL`, or
`DATABASE_URL_POOLED` to the API. The schema is already migrated; the runtime role
only checks its version. Provider and Neatlogs credentials belong to the worker
unless an implemented API feature specifically needs them. No model calls are
executed by the API. Keep existing admission and daily spending defaults.

## Verify

- [ ] Set the actual generated backend origin and deploy with all required values.
- [ ] Confirm startup succeeds and `https://<api-host>/health` returns
  `{"status":"ok"}`.
- [ ] Confirm direct `/api/auth/github/connect` access without the proxy secret
  returns 403; browser login must use the frontend proxy.
- [ ] Configure matching Vercel server settings and GitHub callback settings.
- [ ] Verify deployed login, history, permissions and dispatch in subsequent phases.
- [ ] Record the service URL and deployed commit in the deployment checklist.

A passing health check establishes API startup, not worker readiness or successful
GitHub login. Render's free service can sleep; the Actions worker runs independently.

References: [FastAPI deployment](https://render.com/docs/deploy-fastapi),
[Blueprint fields](https://render.com/docs/blueprint-spec),
[Python version](https://render.com/docs/python-version).
