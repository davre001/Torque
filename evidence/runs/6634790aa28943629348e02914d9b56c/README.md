# Verified Torque demo run

Run ID: `6634790aa28943629348e02914d9b56c`. Status: `completed`. Verified: **true**.

Issue: [kokon #4](https://github.com/GabrieleLozupone/kokon/issues/4). Source revision: `995b078b79819c0049db3eef96fc6bd91b016b12`.

The original source failed the reduced-motion autoplay assertion. Claude proposed a
small HTML edit; all three independent Chromium acceptance assertions then passed,
and Gemini approved criteria 0, 1, and 2. This succeeded on attempt 1, with no agent
recovery retries in this run. Earlier failed development runs are separate runs.

- Models: Gemini 3.5 Flash and Claude Sonnet 4.6 through LiteLLM.
- Model calls: 3. Provider-reported tokens: 23,856.
- Estimated cost: $0.056541, using configured rates (Gemini free-quota rate: $0).
- Agent pipeline wall time: 232.4 seconds, including source download and remote tests; publication occurred later.
- Neatlogs trace ID: `65f1c230ec0f31c423c81d7f0e33ed02`.
- Patch SHA-256: `041ded274194f4acb322f586b5bc9af4c6e22f21fa4d721d4e505350200037b0`.

Published controlled-fork draft PR: [davre001/kokon #1](https://github.com/davre001/kokon/pull/1).

Published commit: `ae520d0100cdac1deaddea191c8bdd72d058ef5d`. The upstream repository was not changed.

## Evidence files

- [Completed run status](run.json)
- [Original pre-publication status](run-before-publication.json)
- [Baseline reproduction](baseline.json)
- [Investigation plan](plan.json)
- [Proposed patch](patch-1.json)
- [Passing browser tests](tests-1.json)
- [First attempt and Gemini review](attempt-1.json)
- [Verified result](verified.json)
- [Integrity manifest and Actions links](manifest.json)

The manifest records hashes of the original artifacts and sanitized exports. Browser
logs include incidental HTTP 404s and connection resets; the structured acceptance
report records exit code 0 and all three assertions passed.

## Remaining dashboard evidence

Add a screenshot and accessible link for the Neatlogs trace. The local trace ID alone
does not establish dashboard ingestion. Add screenshots of the passing Actions job.
Actions links below were matched by timestamps; the backend did not persist their IDs,
so this association is supporting evidence rather than exact run-ID correlation.

- [Torque test b3ecc58ace5742749f717c0eaf01a570](https://github.com/davre001/Torque/actions/runs/38116159905) — success

- [Torque test b4f51f316fb7492e91d6f1b5f6984b0f](https://github.com/davre001/Torque/actions/runs/38116222563) — success
