# Frontend Implementation – Suture

The frontend is intentionally thin. Its only job is to make the agent easy to demo and to show live status, attempts, and the final PR. The real product is the agent loop.

## Goals

- Accept a GitHub issue URL
- Start a Suture run
- Show live status (`investigating` → `implementing` → `verifying` → `recovering` → `done` / `failed`)
- Display attempt history and neatlogs/Entire references when available
- Surface the final PR link
- Be usable in a 3-minute demo without friction

## Stack

- **Backend:** FastAPI (the same process can host the agent orchestration)
- **Frontend:** Single HTML page + lightweight JavaScript (or React/Vite if time allows)
- **Realtime:** Server-Sent Events (SSE) or simple polling every 2 seconds
- **Authentication:** None for the hackathon demo (localhost / temporary deployment)

Alternative if you want even less surface area: Streamlit or Gradio form that calls the same `run_suture()` function.

## Recommended routes

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Serve the UI |
| `POST` | `/api/runs` | Body: `{ "issue_url": "https://..." }` → returns `run_id` |
| `GET` | `/api/runs/{run_id}` | Current status, attempts, and PR URL |
| `GET` | `/api/runs/{run_id}/events` | SSE stream of status updates (optional) |

## UI layout (single screen)

```text
┌─────────────────────────────────────────────────────────┐
│  Turn a GitHub issue into a verified pull request       │
├─────────────────────────────────────────────────────────┤
│  Issue URL  [ https://github.com/.../issues/42       ]  │
│             [ Run Suture ]                              │
├─────────────────────────────────────────────────────────┤
│  Status: Recovery · Attempt 2 of 3                     │
│  ● Investigator  ✓                                      │
│  ● Implementer   ✓ (failed tests)                       │
│  ● Recovery      → changing strategy…                   │
│  ○ Verifier                                             │
├─────────────────────────────────────────────────────────┤
│  Attempts                                               │
│  #1  failed   neatlogs: abc123   "wrong file edited"    │
│  #2  running  neatlogs: def456                          │
├─────────────────────────────────────────────────────────┤
│  Result                                                 │
│  PR: https://github.com/org/repo/pull/87                │
│  Traces · Checkpoints · Plan summary                    │
└─────────────────────────────────────────────────────────┘
```

## Data model the UI needs

```json
{
  "run_id": "run_20261011_001",
  "issue_url": "https://github.com/org/repo/issues/42",
  "status": "recovering",
  "current_agent": "recovery",
  "attempts": [
    {
      "number": 1,
      "status": "failed",
      "trace_id": "...",
      "summary": "Tests failed: AssertionError in test_foo"
    }
  ],
  "pr_url": null,
  "plan_summary": "Update validation in src/auth.py and add regression test"
}
```

Statuses to support: `queued` · `investigating` · `implementing` · `verifying` · `recovering` · `completed` · `failed`.

## Implementation steps (Day 1–2)

1. **Backend skeleton**
   - `POST /api/runs` validates the URL, creates a run record on disk (`runs/{run_id}.json`), and starts the agent in a background task (`asyncio.create_task` or `BackgroundTasks`).
   - `GET /api/runs/{run_id}` reads that JSON and returns it.

2. **Wire the agent**
   - Import the same `run_suture(issue_url, run_id)` function used by the CLI.
   - After every agent step, update the run record (status, attempts, trace IDs). The UI will pick this up via polling or SSE.

3. **Minimal frontend**
   - One `index.html` (or React page) with:
     - Input + button
     - Status badge
     - Attempt list
     - Result / PR area
   - Poll `GET /api/runs/{run_id}` every 2 seconds while the status is not terminal.

4. **SSE (optional polish)**
   - Use `StreamingResponse` to yield events whenever the run record changes. This removes the need for polling and looks better in the demo.

5. **Demo mode**
   - Optional query flag `?demo=1` that pre-fills a known issue URL so you never fumble the paste during the video.

## File layout

```text
frontend/
├── app.py                 # FastAPI app + routes
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── implementation.md      # This file
```

## What *not* to build

- User accounts / OAuth
- Fancy dashboards
- In-browser code editor
- Real-time log streaming of every LLM token (nice-to-have only)

Keep the UI boring and reliable. The wow moment is the agent recovering on screen and the PR appearing—not the frontend chrome.

## Demo checklist for the UI

- [ ] Paste issue → Run starts in under 2 seconds
- [ ] Status updates are visible without refreshing
- [ ] Failed attempt shows a short reason
- [ ] Final PR link is clickable
- [ ] Page still works if the agent takes 2–4 minutes

---

## Practical recommendation for the hackathon

Ship **CLI first**, then a **minimal FastAPI + single-page UI**. Judges only need to see one successful end-to-end run, including a visible recovery and the final pull request.
