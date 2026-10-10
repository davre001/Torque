"""
frontend/app.py — Torque FastAPI application

Routes
------
GET  /                         → serve index.html
POST /api/runs                 → start a new Suture run
GET  /api/runs/{run_id}        → poll current run state
GET  /api/runs/{run_id}/events → SSE stream (optional)

The agent orchestration is imported from the `suture` package.
If the package isn't wired up yet, the run is queued and the
state file is updated so the UI still works for demo purposes.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

# ── Paths ──────────────────────────────────────────────────────────────────

ROOT      = Path(__file__).parent.parent          # project root
RUNS_DIR  = ROOT / "runs"
STATIC    = Path(__file__).parent / "static"

RUNS_DIR.mkdir(exist_ok=True)

# ── FastAPI app ────────────────────────────────────────────────────────────

app = FastAPI(title="Torque", version="0.1.0")


# ── Pydantic models ────────────────────────────────────────────────────────

class StartRunRequest(BaseModel):
    issue_url: HttpUrl


class RunState(BaseModel):
    run_id: str
    issue_url: str
    status: str                       # queued | investigating | implementing | verifying | recovering | completed | failed
    current_agent: str | None = None  # investigator | implementer | verifier | recovery
    attempts: list[dict[str, Any]] = []
    pr_url: str | None = None
    plan_summary: str | None = None
    created_at: str = ""
    updated_at: str = ""


# ── Run state helpers ──────────────────────────────────────────────────────

def run_path(run_id: str) -> Path:
    return RUNS_DIR / f"{run_id}.json"


def load_run(run_id: str) -> dict[str, Any]:
    p = run_path(run_id)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found")
    return json.loads(p.read_text())


def save_run(state: dict[str, Any]) -> None:
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    run_path(state["run_id"]).write_text(json.dumps(state, indent=2))


def initial_state(run_id: str, issue_url: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "run_id": run_id,
        "issue_url": issue_url,
        "status": "queued",
        "current_agent": None,
        "attempts": [],
        "pr_url": None,
        "plan_summary": None,
        "created_at": now,
        "updated_at": now,
    }


# ── Background task ────────────────────────────────────────────────────────

async def run_suture_task(run_id: str, issue_url: str) -> None:
    """
    Wraps the Suture agent loop. Imports are deferred so the UI still
    starts if the agent code isn't available yet.
    """
    state = load_run(run_id)
    try:
        # Try to import and call the real agent
        from suture import run_suture  # type: ignore
        await asyncio.to_thread(run_suture, issue_url, run_id)
    except ImportError:
        # Stub: mark as failed with a clear message so the UI shows something
        state["status"] = "failed"
        state["current_agent"] = None
        state["attempts"] = [
            {
                "number": 1,
                "status": "failed",
                "trace_id": None,
                "summary": "suture package not installed — wire up the agent to make this real.",
            }
        ]
        save_run(state)
    except Exception as exc:
        state["status"] = "failed"
        state["current_agent"] = None
        state["attempts"].append(
            {
                "number": len(state["attempts"]) + 1,
                "status": "failed",
                "trace_id": None,
                "summary": str(exc),
            }
        )
        save_run(state)


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.post("/api/runs", status_code=201)
async def create_run(
    body: StartRunRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    issue_url = str(body.issue_url)
    state = initial_state(run_id, issue_url)
    save_run(state)
    background_tasks.add_task(run_suture_task, run_id, issue_url)
    return {"run_id": run_id}


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    return load_run(run_id)


@app.get("/api/runs/{run_id}/events")
async def run_events(run_id: str):
    """
    SSE stream — yields the run state as a JSON event every 2 seconds
    until the run reaches a terminal status.
    """
    async def event_generator():
        terminal = {"completed", "failed"}
        while True:
            try:
                state = load_run(run_id)
            except HTTPException:
                yield "data: {\"error\": \"run not found\"}\n\n"
                break
            payload = json.dumps(state)
            yield f"data: {payload}\n\n"
            if state.get("status") in terminal:
                break
            await asyncio.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Static files (must come after explicit routes) ─────────────────────────

app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
