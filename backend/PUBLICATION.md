# Publish a verified demo patch

Publication creates a draft PR inside an operator-owned source repository or its fork. It never opens an upstream PR automatically or merges a PR.

1. Create or select your own fork of the demo source. Its default branch must still point at the run's verified `source_sha`. If the branch has advanced, run verification against the new revision first.
2. In the root `.env`, set `TORQUE_PUBLISH_REPOSITORY=davre001/kokon` after creating or confirming that fork. Give `GITHUB_TOKEN` access to this destination with **Contents: read/write** and **Pull requests: read/write**. The token must identify the account that owns the destination.
3. Restart the API after changing environment settings. Publish explicitly from the repository root:

```powershell
.\.venv\Scripts\python.exe -m backend publish 6634790aa28943629348e02914d9b56c
```

Alternatively, use authenticated `POST /api/runs/{run_id}/publish` in the API docs. Use the operator token for API authorization, not the GitHub token.

On success, status becomes `completed` with the actual `pr_url` and published commit SHA. Save that URL in the demo evidence. Until then, the run remains `ready_to_publish`.

The publisher checks saved artifact hashes, the current workspace digest, passing acceptance results, agent approval, repository identity, write permissions, and exact remote tree content before creating the branch and PR. It uses `torque/<run_id>` and a stable PR marker. Repeating a successful request returns the recorded result; retrying after a lost response reconciles the same branch and PR. Conflicting branch content is never overwritten.

Configuration or verification conflicts return HTTP 409; provider/network failures return 502 and retain a safe error. Retry the same run to reconcile uncertain remote results. An active publication lease blocks concurrent publication and cancellation; after a crashed process, its lease expires in 15 minutes. GitHub base changes are checked again before PR creation and against the returned PR; GitHub does not provide an atomic lock on concurrent default-branch updates.

Destination ownership, access, and source/fork relationship are validated with
read-only GitHub requests before the publication destination is locked. A rejected
unrelated repository can therefore be corrected without rerunning the agent.
Once a valid publication is claimed, the destination remains fixed for ambiguous
failures and retries to prevent duplicate PRs across repositories.

A strict legacy repair releases only one prior claim that ended with the explicit
unrelated-destination rejection, has no active owner or saved remote identities,
and has no earlier publication retry. Other failures retain their locks. The
[saved repair evidence](../evidence/gallery/destination-rejection-repair.json)
also confirms no branch or PR existed in the rejected repository before repairing
the gallery demo run. The verified patch remains unchanged; no GitHub writes were
performed during repair. Regression coverage includes invalid first destinations,
active/ambiguous claims, and legacy retry protection; the full suite passed 138
tests with one Windows skip.

Automated tests use mocked GitHub responses. Normal live publication and the controlled live crash/reconciliation trial are verified; see [lifecycle scope](LIFECYCLE_VERIFICATION.md). The crash trial used an isolated database, deterministic fixture review, and clock-advanced lease expiry. Dashboard trace readback and runtime Entire checkpoint links are not asserted by publication.
