"""Authenticated local operator API; execution belongs to the worker."""
from contextlib import asynccontextmanager
import secrets
from typing import Annotated
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from backend.config import Settings
from backend.models import Conflict, SubmitRun, parse_issue
from backend.store import Store

def create_app(settings=None):
    settings = settings or Settings.load()
    store = Store(settings.database)

    @asynccontextmanager
    async def lifespan(app):
        store.initialize()
        yield

    app = FastAPI(title="Torque backend", lifespan=lifespan)
    app.state.store = store

    def operator(authorization: Annotated[str | None, Header()] = None):
        if not settings.operator_token:
            raise HTTPException(503, "Set TORQUE_OPERATOR_TOKEN for local operator access; GitHub login is not implemented yet")
        expected = "Bearer " + settings.operator_token
        if authorization is None or not secrets.compare_digest(authorization.encode(), expected.encode()):
            raise HTTPException(401, "Operator authentication required", headers={"WWW-Authenticate":"Bearer"})
        return "operator"

    def existing(run_id, user):
        if len(run_id) != 32 or any(c not in "0123456789abcdef" for c in run_id):
            raise HTTPException(404, "Run not found")
        record = store.get(run_id,user)
        if record is None:
            raise HTTPException(404, "Run not found")
        return record

    @app.get("/health")
    def health():
        from backend.runtime import readiness
        pipeline = readiness()
        return {"status":"ok", "storage":"sqlite", "execution":"separate-worker",
                "operator_access_configured":bool(settings.operator_token),
                "agent_pipeline_ready":pipeline["configured"],
                "agent_pipeline":pipeline, "github_login_ready":False}

    @app.post("/api/runs", status_code=201)
    def submit(body: SubmitRun, user=Depends(operator),
               idempotency_key: Annotated[str | None, Header(max_length=128)] = None):
        owner, repo, _ = parse_issue(body.issue_url)
        if f"{owner}/{repo}".lower() not in settings.allowed_repositories:
            raise HTTPException(403, "Repository must be explicitly listed in TORQUE_ALLOWED_REPOSITORIES")
        try:
            run_id = store.submit(body.issue_url,user,idempotency_key)
        except Conflict as exc:
            raise HTTPException(409,str(exc)) from exc
        return {"run_id":run_id,"status":store.get(run_id,user)["status"]}

    @app.get("/api/runs")
    def history(user=Depends(operator), limit: int = Query(50,ge=1,le=100)):
        return {"runs":store.history(user,limit)}

    @app.get("/api/runs/{run_id}")
    def status(run_id: str, user=Depends(operator)):
        return existing(run_id,user)

    @app.get("/api/runs/{run_id}/events")
    def events(run_id: str, user=Depends(operator), after: int = Query(0,ge=0)):
        existing(run_id,user)
        return {"events":store.events(run_id,after)}

    @app.post("/api/runs/{run_id}/cancel")
    def cancel(run_id: str, user=Depends(operator)):
        existing(run_id,user)
        try:
            store.cancel(run_id,user)
        except Conflict as exc:
            raise HTTPException(409,str(exc)) from exc
        return existing(run_id,user)

    @app.post("/api/runs/{run_id}/publish")
    def publish(run_id: str, user=Depends(operator)):
        existing(run_id,user)
        raise HTTPException(409,"Publication is unavailable until isolated verification and destination authorization are implemented")

    return app

app = create_app()
