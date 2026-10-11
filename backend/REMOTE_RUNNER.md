# GitHub-hosted Linux runner

No server account or local Docker installation is needed. GitHub Actions provisions an
Ubuntu VM for each test job. Docker isolation runs on that VM. This first implementation
supports reviewed public kokon task profiles: landing-video reduced motion and gallery
keyboard accessibility. Each profile has a fixed editable scope and source policy.

Status: reduced-motion execution and cancellation have live evidence. The new gallery
profile passes local suite calibration and automated contract tests; its updated
workflow must be pushed and its hosted baseline verified before live agent use.
See [gallery setup and evidence](GALLERY_VERIFICATION.md).

## Enable it

1. Commit and push the new .github/workflows/torque-remote-tests.yml to Torque's default branch.
2. In GitHub Settings for Torque, enable Actions if disabled.
3. Create a separate fine-grained token scoped to Torque with Actions read/write and Contents
   read. Store it in the local ignored .env as TORQUE_ACTIONS_TOKEN; never paste it into chat.
4. Set TORQUE_RUNNER=github-actions, TORQUE_ACTIONS_REPOSITORY=davre001/Torque,
   and TORQUE_ACTIONS_REF=main.
5. Set TORQUE_RECIPES_FILE=backend/recipes.remote.json. This reviewed remote recipe
   uses a remote-managed marker; the workflow builds the actual image and records its
   immutable local ID. Local Docker mode rejects this marker.
6. Run backend preflight, then start the API and separate worker.

Each profile's acceptance criteria and editable scope must remain unchanged. Provider keys stay
on the laptop. Only pinned public source and reviewed file replacements are sent to GitHub.
Workflow inputs/artifacts may be visible to repository viewers: private source is unsupported.

Each job uploads a bounded result.json artifact. The backend correlates the random request ID,
source SHA, workflow revision, and acceptance-suite digest. Cancellation requests remote job
cancellation; a ten-minute workflow timeout is a backstop. GitHub queues and image builds count
against the backend wall-time budget. Reduced-motion sandbox compatibility is live-verified;
gallery sandbox compatibility is pending deployment of the updated workflow.

GitHub Actions artifacts expire after one day. Local sanitized attempt artifacts remain available.
PR publication remains a separate explicit action; the runner never publishes a PR.
