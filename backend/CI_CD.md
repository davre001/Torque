# CI and deployment

`Torque CI` runs on pushes and pull requests to `main`, and can also be started
manually from GitHub Actions. It verifies Python tests with a disposable
PostgreSQL service, frontend types, proxy contracts and the Next.js build.
It receives no application or provider secrets and makes no paid model calls.

Vercel's connected Git integration performs frontend deployment.
`frontend/ui/vercel.json` explicitly enables `main` deployments, but cannot
connect a Vercel account or change the project's production branch itself.

In the Vercel project settings, verify:

1. Git repository: `davre001/Torque`.
2. Root directory: `frontend/ui`.
3. Production environment branch tracking: `main`.
4. Deployment history: the latest pushed commit must appear. If it does not,
   use Create Deployment with Git reference `main` and inspect its build logs.

Git-triggered Vercel builds and CI run independently. Passing CI is not yet a
production deployment gate. Protect `main` with the `Torque CI / checks` check
if merges must wait for validation; GitHub account settings are required.
Render remains manually deployed according to `render.yaml`.

The credential-bearing agent worker and independent acceptance workflows remain
separate from this CI workflow. CI never dispatches an agent or publishes a PR.

References: [Vercel Git deployments](https://vercel.com/docs/git),
[Vercel Git configuration](https://vercel.com/docs/project-configuration/git-configuration).
