# Live slider recovery trial

Issue: https://github.com/davre001/kokon/issues/7

Run: `2aa4615e4cbf48deadd99a009b8da11b`. Workflow trace: `23a018f3233355b837448eb9812b232b`.

This real GitHub App user trial used Claude, available Entire runtime context, and the unchanged hosted acceptance suite. No failure was seeded. It tested the corrected instruction to reconstruct the complete fix from the pinned original files on every retry.

Result: **failed after three attempts**. Each attempt passed four of five independent test groups and failed `slider-keys`. Successful live recovery remains unverified. No PR was published.

The final patch reads the slider value using `parseFloat(cmp.getAttribute("aria-valuenow") ?? "50") || 50`. This incorrectly changes a valid zero to 50, breaking keyboard behavior after Home. Recovery retained the complete accessibility changes but did not correct this boundary bug.

First failed-trace readback succeeded through the Neatlogs public API (`failed-trace-1.json`, `recovery-1.json`). Second readback returned HTTP 404 and recovery used local artifacts (`recovery-2.json`). This proves one actual readback, not consistently successful readback or successful repair.

Usage: eight model calls, 51,247 reported tokens, $0.251985 estimated cost. Exact results and hashed artifacts are preserved in `run.json` and adjacent JSON files.
