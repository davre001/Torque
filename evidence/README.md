# Hackathon evidence

Collect verifiable evidence for Torque's issue-to-pull-request agent here.

## Neatlogs

- SDK: Python neatlogs 1.4.26; local Doctor validation passed.
- Synthetic Doctor probe trace: `219851050b14a47507240e0e09bbaa15`.
- The probe timed out during readback; the trace subsequently appeared in the dashboard, as confirmed by the team.
- This synthetic trace does not verify the application's agent instrumentation.
- Successful live agent run: `6634790aa28943629348e02914d9b56c`, with local trace ID `65f1c230ec0f31c423c81d7f0e33ed02`. See the [sanitized demo evidence](runs/6634790aa28943629348e02914d9b56c/README.md).
- Pending: dashboard trace link/screenshots, plus a separately documented failed run and recovery comparison. The saved successful run passed on its first implementation attempt; it does not demonstrate an in-run recovery retry.

## Entire

- Entire is enabled for Codex in this repository.
- The installed Entire hooks for Codex are approved by the repository owner (2026-10-10).
- Captured agent-assisted commit: checkpoint `01M4K5QBAVZ507XR140XFW7586`, linked to [commit `c081469`](https://entire.io/gh/davre001/Torque/commit/c081469dacf1dfa4ac8e291f19a3a4142244f94b).
- Verify captured work with `entire checkpoint list` and `entire checkpoint explain <checkpoint-id>`.

## cfo.ai

- Created the financial model with cfo.ai: [business plan and assumptions](../cfo.ai/README.md), [spreadsheet export](../cfo.ai/torque-financial-plan.xlsx), and [dashboard screenshots](../cfo.ai/screenshots/).
- Covers proposed pricing, inference and infrastructure costs, revenue scenarios, cash funding gaps, runway, and sensitivity. Forecasts are assumptions rather than actual business results; the business README records a discrepancy between the narrative and the exported conservative cash-flow result.

## Demo and submission

- Saved [verified live demo run](runs/6634790aa28943629348e02914d9b56c/README.md): baseline bug reproduced, all three browser assertions passed, and Gemini approved the patch. Three model calls used 23,856 tokens at an estimated $0.056541. Published controlled-fork draft PR: [davre001/kokon #1](https://github.com/davre001/kokon/pull/1).

- Record the issue URL, verified pull request, real test results, and failure-to-recovery sequence.
- Save public build-log links tagged `#neatHack`.
- Include a demo of no more than three minutes covering neatlogs, Entire, and cfo.ai.
- Keep API keys, tokens, and local environment files out of evidence and version control.
