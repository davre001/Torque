import httpx
import pytest
from backend.execution import Recipe
from backend.models import PipelineError, TestResult as RemoteResult
from backend.tools.actions_runner import ActionsRunner

def recipe(tmp_path):
    return Recipe(image="sha256:"+"a"*64,command=["python","test.py"],
        context_files=["site/index.html"],editable_files=["site/index.html"],
        acceptance_criteria=["paused","manual","normal"],suite_directory=str(tmp_path))

def client(handler):
    return httpx.Client(base_url="https://api.github.com",transport=httpx.MockTransport(handler))


def test_default_runner_uses_versioned_reference(tmp_path, monkeypatch):
    monkeypatch.delenv('TORQUE_ACTIONS_REF', raising=False)
    runner = ActionsRunner(recipe(tmp_path), client=client(lambda r: None))
    assert runner.ref == 'torque-runner-v1'
    runner.close()

def test_preflight_requires_actions_token_without_local_docker(tmp_path,monkeypatch):
    monkeypatch.delenv("TORQUE_ACTIONS_TOKEN",raising=False)
    runner = ActionsRunner(recipe(tmp_path),client=client(lambda r:None))
    with pytest.raises(PipelineError,match="TORQUE_ACTIONS_TOKEN"):
        runner.preflight()
    runner.close()

def test_workflow_changes_are_rejected(tmp_path,monkeypatch):
    monkeypatch.setenv("TORQUE_ACTIONS_TOKEN","fixture-token")
    revisions = iter(["a"*40,"b"*40])
    def respond(request):
        return httpx.Response(200,json={"state":"active"} if "/workflows/" in request.url.path else {"sha":next(revisions)})
    runner = ActionsRunner(recipe(tmp_path),client=client(respond))
    runner.preflight()
    with pytest.raises(PipelineError,match="revision changed"):
        runner.preflight()
    runner.close()

def test_remote_scope_is_explicit(tmp_path):
    runner = ActionsRunner(recipe(tmp_path),client=client(lambda r:None))
    with pytest.raises(PipelineError,match="only"):
        runner.bind_source("other","repo","a"*40)
    runner.bind_source("GabrieleLozupone","kokon","a"*40)
    assert runner.source == "a"*40
    runner.close()

def test_demo_fork_requires_identical_reviewed_source_revision(tmp_path):
    runner = ActionsRunner(recipe(tmp_path),client=client(lambda r:None))
    with pytest.raises(PipelineError,match="revision is not reviewed"):
        runner.bind_source("davre001","kokon","a"*40)
    runner.bind_source("davre001","kokon","995b078b79819c0049db3eef96fc6bd91b016b12")
    assert runner.source == "995b078b79819c0049db3eef96fc6bd91b016b12"
    runner.close()


def test_remote_dispatch_returns_correlated_test_result(tmp_path,monkeypatch):
    monkeypatch.setenv("TORQUE_ACTIONS_TOKEN","fixture-token")
    requests = []
    request_id = [None]
    def respond(request):
        requests.append(request)
        if request.method == "POST":
            import json
            body = json.loads(request.content)
            request_id[0] = body["inputs"]["request_id"]
            assert set(body["inputs"]) == {"request_id","source_sha","index_html"}
            assert "fixture-token" not in request.content.decode()
            return httpx.Response(204)
        if "/commits/" in request.url.path:
            return httpx.Response(200,json={"sha":"b"*40})
        if request.url.path.endswith("/runs"):
            return httpx.Response(200,json={"workflow_runs":[
                {"id":17,"display_title":"Torque test "+request_id[0],"status":"completed","head_sha":"b"*40}]})
        return httpx.Response(200,json={"state":"active"})
    runner = ActionsRunner(recipe(tmp_path),client=client(respond),pause=lambda _:None)
    runner.bind_source("GabrieleLozupone","kokon","a"*40)
    (tmp_path/"site").mkdir()
    (tmp_path/"site/index.html").write_text("<html>public fixture</html>")
    runner._result = lambda run,rid: RemoteResult(exit_code=0,output="PASS",command=["remote"],assertions_passed=3)
    result = runner.run(tmp_path,lambda:None)
    assert result.passed
    runner.close()

def test_completed_result_retries_transport_without_redispatch(tmp_path):
    runner = ActionsRunner(recipe(tmp_path),client=client(lambda r: pytest.fail('No dispatch expected')),pause=lambda _:None)
    results = iter([httpx.ReadTimeout('signed secret URL'), RemoteResult(exit_code=0,output='PASS',command=['remote'],assertions_passed=3)])
    def retrieve(*args):
        value = next(results)
        if isinstance(value,Exception): raise value
        return value
    runner._result = retrieve
    assert runner._completed_result({},'fixture',lambda:None).passed
    runner.close()


def test_completed_result_failure_omits_signed_url(tmp_path):
    runner = ActionsRunner(recipe(tmp_path),client=client(lambda r:None),pause=lambda _:None)
    def retrieve(*args): raise httpx.ReadTimeout('signed secret URL')
    runner._result = retrieve
    with pytest.raises(PipelineError,match='result download failed') as error:
        runner._completed_result({},'fixture',lambda:None)
    assert 'signed secret' not in str(error.value)
    runner.close()


def test_redirect_is_preserved_without_forwarding_credentials(tmp_path):
    runner = ActionsRunner(recipe(tmp_path),client=client(lambda request:httpx.Response(
        302,headers={"location":"https://example.blob.core.windows.net/signed"})))
    response = runner._request("GET","/artifact")
    assert response.status_code == 302
    runner.close()

def test_remote_recipe_cannot_run_on_local_docker(tmp_path):
    from backend.tools.sandbox import DockerRunner
    policy = recipe(tmp_path)
    policy.image = "remote-managed"
    with pytest.raises(PipelineError,match="github-actions"):
        DockerRunner(policy).preflight()
