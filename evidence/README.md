# Hackathon evidence

Collect verifiable evidence for Torque's issue-to-pull-request agent here.

## Neatlogs

- SDK: Python neatlogs 1.4.26; local Doctor validation passed.
- Synthetic Doctor probe trace: `219851050b14a47507240e0e09bbaa15`.
- The probe timed out during readback; the trace subsequently appeared in the dashboard, as confirmed by the team.
- This synthetic trace does not verify the application's agent instrumentation.
- Pending: actual failed agent run and recovered successful run, with dashboard links and a comparison of the failure, fix, latency, and cost where available.

## Entire

- Entire is enabled for Codex in this repository.
- The installed Entire hooks for Codex are approved by the repository owner (2026-10-10).
- Captured agent-assisted commit: checkpoint `01M4K5QBAVZ507XR140XFW7586`, linked to [commit `c081469`](https://entire.io/gh/davre001/Torque/commit/c081469dacf1dfa4ac8e291f19a3a4142244f94b).
- Verify captured work with `entire checkpoint list` and `entire checkpoint explain <checkpoint-id>`.

## cfo.ai

- Pending: export a business plan covering pricing, inference and infrastructure costs, revenue, and runway into `business/` and link it here.

## Demo and submission

- Record the issue URL, verified pull request, real test results, and failure-to-recovery sequence.
- Save public build-log links tagged `#neatHack`.
- Include a demo of no more than three minutes covering neatlogs, Entire, and cfo.ai.
- Keep API keys, tokens, and local environment files out of evidence and version control.
