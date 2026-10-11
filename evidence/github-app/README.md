# GitHub App user-run verification

Live permission checks confirmed the encrypted GitHub App user credential for
`davre001` can access `davre001/kokon`, with Contents and Pull requests write
permissions and Issues read. The operator PAT was not used for these checks or
for creating the approved [demo issue #2](https://github.com/davre001/kokon/issues/2).

The fork's default branch is the exact previously tested source commit
`995b078b79819c0049db3eef96fc6bd91b016b12`. Local deployment configuration now
enables this fork with the same reviewed reduced-motion acceptance recipe.
The remote runner rejects other fork revisions: its upstream checkout must be
identical to the submitted fork's complete source tree.

- [x] Verify the actual connected-user App repository permissions.
- [x] Verify source identity and matching reviewed revision.
- [x] Enable the reviewed fork locally and test runner revision enforcement.
- [x] Create a clearly labeled controlled-fork demo issue with user approval.
- [x] Submit the issue from the authenticated workspace browser.
- [x] Verify persisted user ownership, remote baseline/final tests, and model review.
- [x] Export finalized trace readback and sanitized run evidence.
- [x] Verify explicit connected-user PR publication; PR #3 is now merged.
- [x] Verify browser history persistence, confirmed disconnect, and reconnection; user confirmed PR #3 remains and Connect works without refresh.

`permissions.json` contains sanitized live discovery evidence. Permission discovery
and issue creation do not prove successful browser execution or publication.

## First authenticated browser run

Run `4abf1613f01745df8eb4f3b10f6fc3a6` belongs to `github:141245473`, submitted
for fork issue #2 through the workspace. The worker authorized the connected App
user, downloaded the pinned source, and completed remote baseline testing. Gemini
returned HTTP 503 for both investigation requests, so the run failed before any
implementation attempt or PR publication. See `run-failed-503.json`.
Trace ID: `cb993331d55f84c379e0fefa9d975099`.
This is partial live user-flow evidence, not a successful issue-to-PR result.

## Successful connected-user run

Run `b220ce7e5cda4e14963c74fc04ad8711` completed under `github:141245473`
using the approved Claude-only trial mode. The unchanged baseline reproduced the
issue; the first patch passed all three independent browser checks and model review.
The browser publication completed as [PR #3](https://github.com/davre001/kokon/pull/3).
Live readback found its exact verified head commit; the PR is now merged and closed.
Torque did not perform a merge as part of this verification.

The finalized workflow trace `228da4f22bcbe4aeabf7bc797c9d89d1` is OK, with
12 spans and four LLM calls. Acceptance trace `91127a5c3232e6b8ede2fd241d23dc71`
is finalized OK. Provider-accounted usage: 26,057 tokens, estimated cost $0.088683.
The first investigation response needed the bounded format-repair request.
There was one patch attempt and no recovery retry in this run.

Artifacts, run record, PR status, readbacks, and ten artifact checksums are saved
under [the run evidence folder](b220ce7e5cda4e14963c74fc04ad8711/).
Configured credentials and the decrypted App user token were checked absent from
the exported files. Live browser disconnect/reconnection/history was subsequently user-confirmed; see `../browser-acceptance.json`. Publication/disconnect fencing with a live in-flight write remains unverified.

After the merge, the fork's default branch has changed. The reviewed remote runner
will reject a new run against that changed revision; do not reuse the pre-merge
baseline recipe without reviewing the source revision and acceptance task.
