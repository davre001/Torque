import ast
from contextlib import nullcontext
import hashlib
import io
import json
from pathlib import Path
import zipfile
import pytest
from backend.execution import Limits, Recipe
from backend.models import BudgetExceeded, Edit, Patch, PipelineError, Plan, Recovery, Review, TestResult as RunTestResult
from backend.integrations.providers import Budget, Response, StructuredProvider
from backend.pipeline import Pipeline
from backend.store import Store
from backend.tools.files import read_files, safe_path
from backend.tools.patches import apply_patch
from backend.tools.repository import extract_archive
from backend.worker import Worker
from backend.config import Settings

URL = "https://github.com/example/repo/issues/1"
ORIGINAL = 'result = "broken"\n'

def recipe(tmp_path):
    return Recipe(image="python@sha256:"+"a"*64,command=["python","/acceptance/test.py"],
                  context_files=["app.py"],editable_files=["app.py"],
                  acceptance_criteria=["result equals fixed"],suite_directory=str(tmp_path/"suite"))

class FixtureModels:
    def __init__(self,always_fail=False):
        self.edits = 0
        self.recoveries = 0
        self.always_fail = always_fail

    def ask(self,instructions,data,schema):
        if schema is Plan:
            return Plan(summary="Fix result",acceptance_criteria=data["acceptance_criteria"],files=["app.py"])
        if schema is Patch:
            self.edits += 1
            value = "wrong" if self.edits == 1 or self.always_fail else "fixed"
            return Patch(summary="Correct result",edits=[Edit(path="app.py",
                         original_sha256=data["current_files"]["app.py"]["sha256"],
                         content=f'result = "{value}"\n')])
        if schema is Review:
            return Review(approved=True,rationale="Criterion met",satisfied_criteria=[0])
        if schema is Recovery:
            self.recoveries += 1
            assert data["evidence_source"].startswith("local-artifacts")
            return Recovery(strategy="Set the result to fixed")
        raise AssertionError(schema)

class FixtureRunner:
    def preflight(self):
        return None

    def run(self,workspace,checkpoint):
        checkpoint()
        # Independent assertion, outside editable source. Never executes model code.
        module = ast.parse((workspace/"app.py").read_text())
        value = ast.literal_eval(module.body[0].value)
        ok = value == "fixed"
        return RunTestResult(exit_code=0 if ok else 1,
                             output="PASS" if ok else "Expected fixed; actual="+value,
                             command=["fixture-acceptance"],
                             failure_kind=None if ok else "assertion",assertions_passed=1 if ok else 0)

class FixtureGitHub:
    def issue(self,url):
        return {"title":"Fix result","body":"Set result correctly","state":"open","url":url}
    def revision(self,*_):
        return "a"*40

def pipeline_run(tmp_path,models=None,telemetry=None,trace_reader=None):
    store = Store(tmp_path/"db")
    store.initialize()
    run_id = store.submit(URL)
    models = models or FixtureModels()
    def prepare(owner,repo,sha,workspace,checkpoint):
        workspace.mkdir(parents=True)
        (workspace/"app.py").write_text(ORIGINAL)
    pipeline = Pipeline(github=FixtureGitHub(),prepare=prepare,runner=FixtureRunner(),
                        investigator_provider=models,implementer_provider=models,
                        budget=Budget(Limits()),recipe=recipe(tmp_path),
                        workspaces=tmp_path/"work",artifacts=tmp_path/"artifacts",
                        telemetry=telemetry,trace_reader=trace_reader)
    Worker(store,Settings(store.path),pipeline).once()
    return store,run_id,models

def test_real_failure_recovers_and_saves_verified_patch(tmp_path):
    store,run_id,models = pipeline_run(tmp_path)
    run = store.get(run_id)
    assert run["status"] == "ready_to_publish"
    assert run["result"]["verified"] is True
    assert run["result"]["publication_available"] is False
    assert run["pr_url"] is None
    assert models.recoveries == 1
    assert [a["tests_passed"] for a in run["attempts"]] == [False,True]
    assert run["result"]["baseline_passed"] is False
    artifacts = tmp_path/"artifacts"/run_id
    assert json.loads((artifacts/"recovery-1.json").read_text())["evidence_source"] == "local-artifacts"
    for record in run["result"]["artifacts"]:
        assert hashlib.sha256((artifacts/record["name"]).read_bytes()).hexdigest() == record["sha256"]

def test_failed_tests_never_become_verified_and_recovery_is_bounded(tmp_path):
    store,run_id,models = pipeline_run(tmp_path,FixtureModels(always_fail=True))
    run = store.get(run_id)
    assert run["status"] == "failed"
    assert run["result"]["verified"] is False
    assert models.edits == 3 and models.recoveries == 2
    assert len(run["attempts"]) == 3

@pytest.mark.parametrize("name",["../file","/file","C:/file","x\\file",".git/config",".GIT/config",".env","dir/../app.py","CON.txt","dir/trailing."])
def test_files_reject_escape_and_sensitive_paths(tmp_path,name):
    with pytest.raises(PipelineError):
        safe_path(tmp_path,name)

def test_patch_validation_is_all_or_nothing(tmp_path):
    (tmp_path/"app.py").write_text(ORIGINAL)
    sha = hashlib.sha256(ORIGINAL.encode()).hexdigest()
    patch = Patch(summary="Fix",edits=[
        Edit(path="app.py",original_sha256=sha,content="fixed"),
        Edit(path="tests.py",original_sha256=sha,content="weaken assertions")])
    with pytest.raises(PipelineError):
        apply_patch(tmp_path,patch,["app.py"])
    assert (tmp_path/"app.py").read_text() == ORIGINAL

def test_patch_rejects_stale_content(tmp_path):
    (tmp_path/"app.py").write_text(ORIGINAL)
    patch = Patch(summary="Fix",edits=[Edit(path="app.py",original_sha256="0"*64,content="fixed")])
    with pytest.raises(PipelineError):
        apply_patch(tmp_path,patch,["app.py"])

def test_archive_rejects_traversal_before_creating_workspace(tmp_path):
    data = io.BytesIO()
    with zipfile.ZipFile(data,"w") as archive:
        archive.writestr("repo/app.py",ORIGINAL)
        archive.writestr("repo/../../outside.txt","bad")
    with pytest.raises(PipelineError):
        extract_archive(data.getvalue(),tmp_path/"workspace")
    assert not (tmp_path/"workspace").exists()

def test_budget_prevents_request_before_spending():
    budget = Budget(Limits(max_cost_usd=.00001))
    with pytest.raises(BudgetExceeded):
        budget.reserve("prompt",3,15)
    assert budget.calls == 0

def test_explicit_free_quota_still_has_call_and_token_limits():
    budget = Budget(Limits(max_calls=1))
    budget.reserve("prompt",0,0)
    assert budget.estimated_cost == 0
    assert budget.tokens > 0
    with pytest.raises(BudgetExceeded):
        budget.reserve("prompt",0,0)

def test_missing_usage_retains_reservation_and_stops():
    class Adapter:
        def complete(self,*_):
            return Response('{"strategy":"fix"}',None,None,"fixture")
    budget = Budget(Limits())
    provider = StructuredProvider(Adapter(),budget,3,15,lambda:None)
    with pytest.raises(PipelineError,match="usage"):
        provider.ask("recover",{},Recovery)
    assert budget.calls == 1 and budget.estimated_cost > 0

def test_transport_retries_are_charged_and_distinct_from_recovery():
    class RateLimited(Exception):
        status_code = 429
    class Adapter:
        calls = 0
        def complete(self,*_):
            self.calls += 1
            if self.calls == 1:
                raise RateLimited()
            return Response('{"strategy":"fix"}',100,20,"fixture")
    budget = Budget(Limits())
    provider = StructuredProvider(Adapter(),budget,3,15,lambda:None,transport_retries=1)
    assert provider.ask("recover",{},Recovery).strategy == "fix"
    assert budget.calls == 2

def test_docker_missing_fails_before_execution(tmp_path,monkeypatch):
    from backend.tools.sandbox import DockerRunner
    monkeypatch.setattr("backend.tools.sandbox.shutil.which",lambda _:None)
    with pytest.raises(PipelineError,match="Docker"):
        DockerRunner(recipe(tmp_path)).preflight()

def test_global_worker_concurrency_is_one(tmp_path):
    store = Store(tmp_path/"db")
    store.initialize()
    store.submit(URL)
    store.submit(URL.replace("/1","/2"))
    assert store.claim(60) is not None
    assert store.claim(60) is None

def test_completed_requires_recorded_pr_url(tmp_path):
    from backend.models import Conflict, Status
    store = Store(tmp_path/"db")
    store.initialize()
    run_id = store.submit(URL)
    _, owner = store.claim(60)
    with pytest.raises(Conflict,match="PR URL"):
        store.update(run_id,owner,Status.COMPLETED)
    assert store.get(run_id)["status"] == "queued"

def test_infrastructure_failure_never_counts_as_bug_reproduction(tmp_path):
    store = Store(tmp_path/"db")
    store.initialize()
    run_id = store.submit(URL)
    class BrokenRunner(FixtureRunner):
        def run(self,*args):
            return RunTestResult(exit_code=1,output="Browser unavailable",command=["fixture"],
                                 failure_kind="infrastructure")
    class NoModelCalls:
        def ask(self,*args):
            raise AssertionError("Infrastructure failure must stop before model calls")
    def prepare(owner,repo,sha,workspace,checkpoint):
        workspace.mkdir(parents=True)
        (workspace/"app.py").write_text(ORIGINAL)
    pipeline = Pipeline(github=FixtureGitHub(),prepare=prepare,runner=BrokenRunner(),
                        investigator_provider=NoModelCalls(),implementer_provider=NoModelCalls(),
                        budget=Budget(Limits()),recipe=recipe(tmp_path),
                        workspaces=tmp_path/"work",artifacts=tmp_path/"artifacts")
    Worker(store,Settings(store.path),pipeline).once()
    assert store.get(run_id)["status"] == "failed"
    assert "Baseline did not reproduce" in store.get(run_id)["error"]

def test_telemetry_mask_omits_prompts_and_redacts_credentials():
    from backend.integrations.neatlogs import Telemetry
    telemetry = Telemetry("",("secret-key",))
    cleaned = telemetry.mask({"attributes":{"input.value":"source code",
                                          "model":"fixture","description":"secret-key"}})
    assert cleaned["attributes"]["input.value"] == "[content omitted]"
    assert cleaned["attributes"]["description"] == "[redacted]"
