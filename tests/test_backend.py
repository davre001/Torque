import concurrent.futures
import threading
import time
import pytest
from fastapi.testclient import TestClient
from backend.api import create_app
from backend.config import Settings
from backend.models import Conflict, LeaseLost, Status, SubmitRun
from backend.store import Store
from backend.worker import Worker

URL = "https://github.com/GabrieleLozupone/kokon/issues/4"

@pytest.fixture
def store(tmp_path):
    db = Store(tmp_path / "queue.sqlite3")
    db.initialize()
    return db

@pytest.mark.parametrize("url", [
    "http://github.com/a/b/issues/1", "https://githubXcom/a/b/issues/1",
    "https://github.com/a/../issues/1", "https://github.com/a/b/issues/0",
    "https://github.com/a/b/issues/1?x=2", "https://github.com/a/b/pull/1",
    "https://github.com/a/b/issues/1/../../foo",
])
def test_reject_invalid_urls(url):
    with pytest.raises(ValueError):
        SubmitRun(issue_url=url)

def test_submission_survives_restart_and_is_idempotent(store):
    run_id = store.submit(URL,"alice","request-1")
    assert Store(store.path).get(run_id,"alice")["status"] == "queued"
    assert store.submit(URL,"alice","request-1") == run_id
    with pytest.raises(Conflict):
        store.submit(URL.replace("/4","/5"),"alice","request-1")
    assert store.get(run_id,"bob") is None
    assert store.history("bob") == []

def test_only_one_competing_worker_claims(store):
    store.submit(URL)
    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        claims = list(pool.map(lambda _: store.claim(60),range(4)))
    assert sum(claim is not None for claim in claims) == 1

def test_expired_owners_cannot_write_or_renew(store):
    now = [1000.]
    store.clock = lambda: now[0]
    run_id = store.submit(URL)
    _, owner = store.claim(60)
    now[0] += 61
    with pytest.raises(LeaseLost):
        store.update(run_id,owner,Status.COMPLETED)
    with pytest.raises(LeaseLost):
        store.heartbeat(run_id,owner,60)
    assert store.claim(60) is None
    assert store.get(run_id)["status"] == "interrupted"

def test_cancel_queued_prevents_execution(store):
    run_id = store.submit(URL,"alice")
    store.cancel(run_id,"alice")
    assert store.claim(60) is None
    assert store.get(run_id)["status"] == "cancelled"

def test_worker_cancellation_while_processing(store):
    run_id = store.submit(URL)
    started = threading.Event()
    def processor(db, rid, owner, checkpoint):
        db.update(rid,owner,Status.INVESTIGATING)
        started.set()
        while True:
            time.sleep(.01)
            checkpoint()
    worker = Worker(store,Settings(store.path),processor)
    thread = threading.Thread(target=worker.once)
    thread.start()
    assert started.wait(2)
    store.cancel(run_id,"operator")
    thread.join(2)
    assert not thread.is_alive()
    assert store.get(run_id)["status"] == "cancelled"

def test_worker_failure_does_not_expose_exception_secrets(store):
    run_id = store.submit(URL)
    def processor(*args):
        raise RuntimeError("secret-provider-key")
    Worker(store,Settings(store.path),processor).once()
    assert store.get(run_id)["status"] == "failed"
    assert "secret-provider-key" not in str(store.get(run_id))

def test_api_queue_auth_history_events_and_conflicts(tmp_path,monkeypatch):
    # Readiness must not depend on the developer's real .env configuration.
    monkeypatch.setenv("GEMINI_MODEL","")
    app = create_app(Settings(tmp_path/"api.db","local-test-token",
                              allowed_repositories=("gabrielelozupone/kokon",)))
    headers = {"Authorization":"Bearer local-test-token", "Idempotency-Key":"request-1"}
    with TestClient(app) as client:
        assert client.get("/api/runs").status_code == 401
        assert client.get("/health").json()["agent_pipeline_ready"] is False
        response = client.post("/api/runs",json={"issue_url":URL},headers=headers)
        assert response.status_code == 201
        run_id = response.json()["run_id"]
        assert client.post("/api/runs",json={"issue_url":URL},headers=headers).json()["run_id"] == run_id
        assert client.post("/api/runs",json={"issue_url":URL.replace("/4","/5")},headers=headers).status_code == 409
        assert client.get(f"/api/runs/{run_id}",headers=headers).json()["status"] == "queued"
        assert len(client.get("/api/runs",headers=headers).json()["runs"]) == 1
        events = client.get(f"/api/runs/{run_id}/events",headers=headers).json()["events"]
        assert events[0]["status"] == "queued"
        assert client.get(f"/api/runs/{run_id}/events?after={events[0]['id']}",headers=headers).json()["events"] == []
        assert client.post(f"/api/runs/{run_id}/publish",headers=headers).status_code == 409
        assert client.post(f"/api/runs/{run_id}/cancel",headers=headers).json()["status"] == "cancelled"
        assert client.post(f"/api/runs/{run_id}/cancel",headers=headers).status_code == 409
        assert client.get("/api/runs/not-a-run",headers=headers).status_code == 404
        assert client.post("/api/runs",json={"issue_url":"https://github.com/other/repo/issues/1"},headers=headers).status_code == 403

def test_api_fails_closed_without_operator_configuration(tmp_path):
    with TestClient(create_app(Settings(tmp_path/"db"))) as client:
        assert client.get("/api/runs").status_code == 503

def test_readonly_github_adapter_rejects_pull_requests():
    import httpx
    from backend.integrations.github import GitHub
    paths = []
    def respond(request):
        paths.append(request.url.path)
        return httpx.Response(200,json={"title":"Example","state":"open","pull_request":{}})
    client = GitHub(transport=httpx.MockTransport(respond))
    try:
        with pytest.raises(ValueError):
            client.issue(URL)
        assert paths == ["/repos/GabrieleLozupone/kokon/issues/4"]
    finally:
        client.close()

def test_issue_milestone_has_no_false_verified_outcome(store,monkeypatch):
    from backend.orchestrator import investigate
    monkeypatch.setattr("backend.orchestrator.GitHub.issue",
                        lambda self,url: {"title":"Fix autoplay","state":"open","url":url})
    run_id = store.submit(URL)
    Worker(store,Settings(store.path),investigate).once()
    record = store.get(run_id)
    assert record["status"] == "failed"
    assert record["result"]["verified"] is False
    assert record["pr_url"] is None

def test_long_operation_renews_lease(store):
    run_id = store.submit(URL)
    settings = Settings(store.path,lease_seconds=3,heartbeat_seconds=1)
    def slow(db,rid,owner,checkpoint):
        time.sleep(3.2)
        checkpoint()
        db.update(rid,owner,Status.READY,result={"fixture":True})
    Worker(store,settings,slow).once()
    assert store.get(run_id)["status"] == "ready_to_publish"
