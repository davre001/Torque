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

Implemented tests use mocked GitHub responses. A live PR has not been created as part of implementation. Dashboard trace readback and runtime Entire checkpoint links are not asserted by publication.
