"""Authenticated local operator API; execution belongs to the worker."""
from contextlib import asynccontextmanager
import secrets
from typing import Annotated
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, Request
from backend.config import Settings
from backend.models import Conflict, AdmissionDenied, SubmitRun, parse_issue
from backend.store import Store
from backend.repository_setup import SetupConfig
from pydantic import BaseModel, ConfigDict

class SetupRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    framework: str
    test_files: list[str]
    editable_files: list[str] | None = None

def create_app(settings=None):
    settings = settings or Settings.load()
    store = Store(settings.database)
    from backend.github_auth import GitHubAuth
    auth = GitHubAuth(store)
    from backend.admission import Admission
    admission = Admission.load()
    from backend.public_boundary import PublicPolicy, PublicBoundary
    public_policy = PublicPolicy.load(settings, auth)

    @asynccontextmanager
    async def lifespan(app):
        store.initialize()
        auth.initialize()
        from backend.cloud_preflight import check
        cloud=check(store)
        if not cloud['configured']:
            raise ValueError('Invalid cloud storage/dispatch configuration')
        yield

    app = FastAPI(title="Torque backend", lifespan=lifespan)
    if public_policy:
        from starlette.middleware.trustedhost import TrustedHostMiddleware
        app.add_middleware(PublicBoundary, store=store, policy=public_policy)
        import os
        from urllib.parse import urlparse
        backend_origin = os.getenv('TORQUE_BACKEND_ORIGIN','')
        hosts = [public_policy.host]
        if backend_origin:
            parsed = urlparse(backend_origin)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {'','/'} or not os.getenv('TORQUE_PROXY_SECRET'):
                raise ValueError('Backend proxy requires an HTTPS origin and TORQUE_PROXY_SECRET')
            hosts.append(parsed.hostname)
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts, www_redirect=False)
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(CORSMiddleware,allow_origins=[auth.origin],allow_credentials=True,
                       allow_methods=["GET","POST"],allow_headers=["Content-Type","X-CSRF-Token","Idempotency-Key"])

    @app.middleware("http")
    async def private_responses(request, call_next):
        response=await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"]="no-store"
            response.headers["Referrer-Policy"]="no-referrer"
        return response

    app.state.store = store
    app.state.settings = settings
    app.state.github_auth = auth
    auth.routes(app)

    @app.post('/api/repositories/{owner}/{repo}/setup', status_code=202)
    def configure_repository(owner: str, repo: str, body: SetupRequest, request: Request):
        from backend.repository_setup import start_setup
        from backend.models import PipelineError
        user = auth.authenticate(request)
        try:
            values = body.model_dump()
            if body.editable_files is None:
                from backend.repository_detection import validation_source
                values['editable_files'] = validation_source(auth, user, f'{owner}/{repo}', values)
            from pydantic import ValidationError
            try:
                config = SetupConfig.model_validate(values)
            except ValidationError:
                raise HTTPException(422, 'Invalid supported test configuration') from None
            return start_setup(store, auth, user, f'{owner}/{repo}', config)
        except PipelineError as exc:
            raise HTTPException(502, str(exc)) from None

    @app.post('/api/repositories/{owner}/{repo}/setup/automatic', status_code=202)
    def automatic_repository(owner: str, repo: str, request: Request):
        from backend.repository_detection import detect_repository
        from backend.repository_setup import setup_record, public_setup, start_setup
        from backend.models import PipelineError
        user = auth.authenticate(request)
        repository = f'{owner}/{repo}'.lower()
        auth.authorize(user, repository)
        previous = setup_record(store, user, repository)
        if previous:
            return public_setup(previous)
        try:
            config = detect_repository(auth, user, repository)
            return start_setup(store, auth, user, repository, config)
        except PipelineError as exc:
            raise HTTPException(502, str(exc)) from None

    @app.get('/api/repositories/{owner}/{repo}/setup')
    def repository_setup(owner: str, repo: str, request: Request):
        from backend.repository_setup import refresh_setup
        return refresh_setup(store, auth, auth.authenticate(request), f'{owner}/{repo}')

    def operator(request: Request, authorization: Annotated[str | None, Header()] = None):
        if authorization is None and request.cookies.get(auth.cookie):
            return auth.authenticate(request)
        if public_policy:
            raise HTTPException(401, "GitHub login required")
        if not settings.operator_token:
            raise HTTPException(503, "Set TORQUE_OPERATOR_TOKEN for local operator access; or configure GitHub App login")
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
        if public_policy:
            return {"status":"ok"}
        from backend.runtime import readiness
        pipeline = readiness()
        return {"status":"ok", "storage":"postgresql" if store.database.postgres else 'sqlite', "execution":"separate-worker",
                "operator_access_configured":bool(settings.operator_token),
                "agent_pipeline_ready":pipeline["configured"],
                "agent_pipeline":pipeline, "github_login_ready":auth.configured}

    @app.post("/api/runs", status_code=201)
    def submit(body: SubmitRun, user=Depends(operator),
               idempotency_key: Annotated[str | None, Header(max_length=128)] = None):
        owner, repo, _ = parse_issue(body.issue_url)
        from backend.repository_setup import setup_record, setup_recipe
        setup = setup_record(store, user, f'{owner}/{repo}') if user != 'operator' else None
        onboarded = setup_recipe(setup) if setup and setup['status'] == 'ready' else None
        if user == 'operator' and f"{owner}/{repo}".lower() not in settings.allowed_repositories:
            raise HTTPException(403, "Repository must be explicitly listed in TORQUE_ALLOWED_REPOSITORIES")
        if user != 'operator':
            auth.authorize(user,f'{owner}/{repo}')
            from backend.repository_policy import eligibility, reviewed_recipes
            policy = eligibility(f'{owner}/{repo}', None, reviewed_recipes()) if onboarded is None else {'run_supported': True}
            if not policy['run_supported']:
                raise HTTPException(422, policy['run_reason'])
        try:
            run_id = store.submit(body.issue_url,user,idempotency_key,admission=admission,repository_setup=setup if onboarded else None)
        except AdmissionDenied as exc:
            raise HTTPException(429,str(exc)) from None
        except Conflict as exc:
            raise HTTPException(409,str(exc)) from exc
        if __import__('os').getenv('TORQUE_WORKER_DISPATCH','local') == 'github-actions':
            from backend.dispatch import Dispatcher
            dispatcher = Dispatcher(store)
            try: dispatcher.dispatch(run_id)
            finally: dispatcher.close()
        return {"run_id":run_id,"status":store.get(run_id,user)["status"]}

    @app.get("/api/runs")
    def history(user=Depends(operator), limit: int = Query(50,ge=1,le=100)):
        return {"runs":store.history(user,limit)}

    @app.get("/api/runs/{run_id}")
    def status(run_id: str, background_tasks: BackgroundTasks, user=Depends(operator)):
        current = existing(run_id,user)
        if current['status'] == 'queued' and not current.get('cancel_requested') and __import__('os').getenv('TORQUE_WORKER_DISPATCH','local') == 'github-actions':
            def retry_dispatch():
                from backend.dispatch import Dispatcher
                dispatcher = Dispatcher(store)
                try: dispatcher.dispatch(run_id)
                finally: dispatcher.close()
            background_tasks.add_task(retry_dispatch)
        return current

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
    def publish(run_id: str, user=Depends(operator), destination: str | None = Query(None,max_length=140)):
        existing(run_id,user)
        from backend.publication import publish_run
        from backend.models import PipelineError
        try:
            return publish_run(store,run_id,user,destination=destination)
        except Conflict as exc:
            raise HTTPException(409,str(exc)) from None
        except PipelineError as exc:
            raise HTTPException(502,str(exc)) from None

    return app

app = create_app()
