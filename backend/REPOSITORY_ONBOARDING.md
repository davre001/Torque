# Automatic repository onboarding

The workspace automatically requests test detection for newly connected repositories without a reviewed recipe or saved setup. The CSRF-protected `POST /api/repositories/{owner}/{repo}/setup/automatic` endpoint detects npm/pnpm test packages (including nested workspace packages) or pytest test files and starts the hosted validator. Common Vitest and Jest defaults are normalized to a single managed test run. Repeated requests reuse saved validation instead of dispatching another workflow. Detection never executes a command on the API host.

Repositories show **Connected — detecting tests**, **Checking tests**, then **Ready to run** only after successful validation. Unsupported commands, missing tests, or unrecognized test configurations require manual setup. Detection automatically freezes a bounded subset of up to 10 test/configuration files; validation covers that subset, not every test in a large repository. Validation capacity is retried while the workspace remains open; failed validation is not automatically resubmitted. Manual Repository tests controls appear only when detection or validation needs help. Existing public-repository, authorization, spending, file-size, and validation-rate limits remain in force.

Each signed-in user can enable an installed **public** GitHub repository through
**Workspace → Repository access → Set up tests**. Existing reviewed Kokon demo
recipes continue to work. User setups do not require deployment-wide allowlist edits.

1. Choose the managed test environment.
2. List explicit test files, test helpers and configuration to freeze.
3. Torque discovers source files automatically; no edit paths are required.
4. Select **Validate and enable**. A separate hosted job runs the test suite.
5. The panel polls for the result. A passing, nonempty suite enables this repository
   for this user. Failures expose bounded diagnostics and leave it disabled.

Configuration is stored in the shared database. GitHub installation permissions
are checked again when validating, submitting, executing and publishing. Another
user's setup never grants access or enables that user's repositories. Changes to
test configuration are blocked while that user has an unfinished repository run,
including a run awaiting publication.

## Supported environments

| Environment | Requirements |
| --- | --- |
| Node.js 24 / npm or pnpm | Automatically finds a package with Vitest, Jest or `node --test`, including packages below the workspace root. Freezes package manifests, lockfiles, configuration and a bounded test subset. pnpm requires a pinned `packageManager` version and root `pnpm-lock.yaml`. Installs dependencies with lifecycle scripts disabled, then runs tests without networking. |
| Python 3.11 / pytest 8.3.5 | Explicit Python test files plus test configuration/helpers. Python standard library and pytest are available; project-specific third-party dependencies are not installed. |

The Node setup installs locked dependencies with lifecycle hooks disabled in a
credential-free, resource-limited container. Tests run separately with networking
disabled, a read-only source mount, an unprivileged UID, limited CPU/memory/processes,
and a bounded writable temporary filesystem. Repository code never runs in the
credential-bearing coordinator or API process. No arbitrary caller-provided host
command or Dockerfile is accepted.

The test files are frozen at the validation commit. Agent attempts use the current
source commit while restoring those frozen test/configuration files. The agent
can modify only the configured source files. Revalidate deliberately when changing
the suite. The test result means the selected tests pass; it does not establish
that those tests fully cover the issue or the repository.

Generic repository diagnostics currently report one named **Frozen repository test
suite** case, with captured output and assertion details. Existing Kokon profiles
retain their individual acceptance-case spans.

Validation is limited to three concurrent jobs across the deployment, ten configured
repositories per user, and three validation attempts per repository per UTC day.
Jobs time out, and missing artifacts, changed workflow revisions, empty suites,
and invalid result identities cannot activate a setup. Refreshing a setup after
15 minutes records an expired validation as failed.

## Rollout order

These changes require database schema **2** and an updated remote test workflow.
Do not deploy the frontend alone.

1. Apply the migration with the owner/migration credential:
   `python -m backend migrate`. It adds `repository_setups` and preserves existing
   users, runs and artifacts. Runtime credentials remain DML-only.
2. Refresh the runtime role's grants using `python -m backend.database_roles`.
   Check that `repository_setups` is covered. Preserve the existing runtime role;
   do not copy the migration credential to Render or Actions.
3. Ship `.github/workflows/torque-remote-tests.yml` and the managed runner files to
   the configured `TORQUE_ACTIONS_REF`. API preflight refuses an old workflow.
4. Deploy the API and Actions worker code together. Use the shared database and
   `TORQUE_RUNNER=github-actions` with a workflow dispatch/read credential.
5. Deploy the frontend, including the new same-origin `/api/repositories/*/setup`
   proxy routes.
6. Verify with a small public repository: passing tests activate it; a forced
   failure and an empty suite do not. Then exercise a complete agent run and explicit
   PR publication with that repository's user authorization.

Existing encrypted schema-1 backups remain readable: restore adds an empty
repository setup table and upgrades the schema version. Take a fresh backup after
migration. Roll back application code only with a compatible schema strategy;
older code checks specifically for schema 1.

Local verification covers authenticated activation/failure/ownership/revision
checks, schema-1 migration preservation and actual Python/Node reporter processes.
Container execution and the deployed end-to-end flow must also be verified in
the hosted environment before describing this feature as production-verified.

## Source discovery per issue

Each managed run inventories supported source files from its pinned checkout, excluding secrets, hidden paths, dependency/build directories, tests, configuration and symlinks. The investigator selects up to ten relevant files from that inventory before reading bounded source content. These paths may differ from the bootstrap paths used during onboarding validation. The worker records the selected scope in a hashed artifact; publication checks that evidence and the verified content before allowing edits. The runtime still bounds each investigation to 100 KB of source content and 2,000 candidate paths. This removes user file selection, not execution resource limits.

## Python dependency preparation

Python detection includes requirements.txt alongside Python tests and excludes JavaScript tests. Managed repository jobs use the fixed torque-repository-runner-v4 tag (separate from reviewed demo runners). Frozen public requirements are installed as binary wheels in a credential-free, unprivileged container with bounded time and memory; build scripts, local paths, alternative indexes and URL dependencies are rejected. Tests run separately with networking disabled, project roots on PYTHONPATH and dotenv loading disabled. A failed setup can be retried explicitly through Reconfirm Torque access; existing validation capacity and daily attempt limits still apply.

The v4 managed runner preserves repository identity even if preparation fails and installs wheels with the coordinator UID so permission normalization and cleanup work. The credential-free hosted Encore smoke workflow exercises this Linux ownership path.

Native Python wheel extensions load from the read-only dependency bind mount rather than the no-exec temporary filesystem; dependencies are excluded from the temporary project copy.
