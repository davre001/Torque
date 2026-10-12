"""Bounded issue-to-verified-patch execution; publication is not automatic."""
from contextlib import nullcontext
from pathlib import Path
import hashlib
import logging
from backend.agents import investigator, implementer, verifier, recovery
from backend.artifacts import Artifacts
from backend.models import PipelineError, Status, parse_issue
from backend.tools.files import read_files
from backend.tools.patches import apply_patch

log = logging.getLogger(__name__)

class Pipeline:
    def __init__(self, *, github, prepare, runner, investigator_provider,
                 implementer_provider, budget, recipe, workspaces, artifacts,
                 telemetry=None, secrets=(), trace_reader=None):
        self.github, self.prepare, self.runner = github,prepare,runner
        self.investigator_provider, self.implementer_provider = investigator_provider,implementer_provider
        self.budget, self.recipe = budget,recipe
        self.workspaces, self.artifacts = Path(workspaces),Path(artifacts)
        self.telemetry, self.secrets = telemetry,secrets
        self.trace_reader = trace_reader

    def span(self,name,kind="TOOL",**attrs):
        return self.telemetry.span(name,kind,**attrs) if self.telemetry else nullcontext(None)

    def __call__(self,store,run_id,owner,checkpoint):
        artifacts = Artifacts(self.artifacts/run_id,self.secrets)
        result = {"verified":False,"artifacts":[],"recovery_evidence_source":"local-artifacts"}

        def check():
            checkpoint()
            self.budget.check()

        def save(name,value):
            record = artifacts.write(name,value)
            result["artifacts"].append(record)
            return record

        def transition(status,**kwargs):
            check()
            result["budget"] = self.budget.snapshot()
            store.update(run_id,owner,status,result=artifacts.sanitize(result),**kwargs)

        with self.span("github-issue-to-pr","WORKFLOW",run_id=run_id) as root_span:
            if root_span is not None:
                result["trace_id"] = format(root_span.get_span_context().trace_id,"032x")
            try:
                check()
                self.runner.preflight()
                result["test_image"] = self.recipe.image
                result["acceptance_suite_sha256"] = getattr(self.runner,"suite_sha256",None)
                transition(Status.INVESTIGATING)
                run = store.get(run_id)
                source_owner,repo,_ = parse_issue(run["issue_url"])
                with self.span("fetch-issue"):
                    log.info("Fetching issue and source revision for run %s",run_id)
                    issue = self.github.issue(run["issue_url"])
                    if issue["state"] != "open":
                        raise PipelineError("Issue is closed; choose an open issue")
                    sha = self.github.revision(source_owner,repo)
                result["source_sha"], result["source_repository"] = sha,f"{source_owner}/{repo}"
                if hasattr(self.runner,"bind_source"):
                    self.runner.bind_source(source_owner,repo,sha)
                workspace = self.workspaces/run_id
                with self.span("prepare-pinned-source"):
                    self.prepare(source_owner,repo,sha,workspace,check)
                context = read_files(workspace,self.recipe.context_files)
                # Editable files must be present in context; test suite is outside workspace.
                if any(path not in context for path in self.recipe.editable_files):
                    raise PipelineError("Every editable file must also be a context file")
                originals = {name:context[name]["content"] for name in self.recipe.editable_files}
                from backend.integrations.entire import EntireContext
                with self.span('entire-target-context'):
                    entire_context=EntireContext().search(result['source_repository'],sha,issue.get('title','issue investigation'),context,
                        next(iter(self.recipe.investigation_terms.values()),[None])[0])
                save('entire-context',entire_context)
                result['entire_context_status']=entire_context['status']
                with self.span("baseline-tests"):
                    log.info("Starting baseline tests for run %s",run_id)
                    baseline = self.runner.run(workspace,check)
                    from backend.integrations.test_diagnostics import trace_test_result
                    trace_test_result(self.telemetry, baseline)
                save("baseline",baseline.model_dump())
                result["baseline_passed"] = baseline.passed
                result["acceptance_suite_sha256"] = getattr(self.runner,"suite_sha256",None)
                if getattr(self.runner,"test_image",None):
                    result["test_image"] = self.runner.test_image
                if baseline.failure_kind in {"infrastructure","timeout"}:
                    raise PipelineError("Baseline did not reproduce an acceptance failure; test infrastructure failed")
                if self.recipe.require_baseline_failure and (baseline.passed or baseline.failure_kind != "assertion"):
                    raise PipelineError("Baseline did not reproduce an acceptance failure; investigate before spending model credits")
                with self.span("investigator","AGENT"):
                    plan = investigator.investigate(self.investigator_provider,issue,context,self.recipe,artifacts.sanitize(entire_context))
                result["plan"] = plan.model_dump()
                save("plan",plan.model_dump())
                strategy = None
                for number in range(1,self.budget.limits.recovery_retries+2):
                    transition(Status.IMPLEMENTING)
                    # Recovery starts from the pinned source, avoiding compounded partial fixes.
                    from backend.tools.files import safe_path
                    for name,text in originals.items():
                        safe_path(workspace,name).write_bytes(text.encode())
                    current = read_files(workspace,self.recipe.context_files)
                    if self.recipe.investigation_terms:
                        from backend.tools.files import investigation_context
                        current = investigation_context(current,self.recipe.investigation_terms)
                    with self.span("implementer","AGENT",attempt=number):
                        patch = implementer.implement(self.implementer_provider,plan,current,strategy)
                    with self.span("apply-approved-edits"):
                        check()
                        patch_hash = apply_patch(workspace,patch,self.recipe.editable_files,self.budget.limits.max_patch_bytes)
                    save(f"patch-{number}",patch.model_dump())
                    transition(Status.VERIFYING)
                    attempt_name = f'acceptance-tests-{run_id}-{number}'
                    attempt_context = self.telemetry.attempt(attempt_name, attempt=number, run_id=run_id) if self.telemetry else nullcontext(None)
                    with attempt_context as test_span:
                        tests = self.runner.run(workspace,check)
                        if tests.passed and tests.assertions_passed != len(self.recipe.acceptance_criteria):
                            tests.failure_kind = 'infrastructure'
                        trace_test_result(self.telemetry, tests)
                        if test_span is not None:
                            from opentelemetry.trace import Status as SpanStatus, StatusCode
                            test_span.set_attribute('torque.assertions_passed', tests.assertions_passed)
                            test_span.set_attribute('torque.failure_kind', tests.failure_kind or 'none')
                            test_span.set_attribute('torque.acceptance_diagnostics',
                                                    artifacts.sanitize(tests.output[-4000:]))
                            test_span.set_status(SpanStatus(StatusCode.OK if tests.passed else StatusCode.ERROR,
                                                          None if tests.passed else 'Independent acceptance tests failed'))
                    attempt_trace = format(test_span.get_span_context().trace_id, '032x') if test_span is not None else None
                    if tests.passed and tests.assertions_passed != len(self.recipe.acceptance_criteria):
                        tests.failure_kind = "infrastructure"
                    save(f"tests-{number}",tests.model_dump())
                    if tests.failure_kind in {"infrastructure","timeout"}:
                        transition(Status.VERIFYING,attempt={"number":number,"patch_sha256":patch_hash,
                                   "tests_passed":False,"failure_kind":tests.failure_kind})
                        raise PipelineError("Acceptance test infrastructure failed; stopping without agent recovery")
                    changed = read_files(workspace,self.recipe.context_files)
                    with self.span("verifier","AGENT",attempt=number):
                        review = verifier.verify(self.investigator_provider,plan,changed,tests,
                                                 recipe=self.recipe,originals=originals)
                    attempt = {"number":number,"patch_sha256":patch_hash,"tests_passed":tests.passed,
                               "review":review.model_dump(),"budget":self.budget.snapshot(),
                               "trace_id":result.get("trace_id"), "test_trace_id":attempt_trace}
                    attempt = artifacts.sanitize(attempt)
                    save(f"attempt-{number}",attempt)
                    if tests.passed and review.approved:
                        check()
                        # Digest exact source bytes verified, not an invented Git commit SHA.
                        digest = hashlib.sha256()
                        for name,record in sorted(changed.items()):
                            digest.update(name.encode()+b"\0"+record["content"].encode())
                        result.update(verified=True,verified_content_sha256=digest.hexdigest(),
                                      patch_sha256=patch_hash,summary=patch.summary,
                                      publication_available=False)
                        if root_span is not None:
                            root_span.set_attribute("torque.status","ready_to_publish")
                        save("verified",result)
                        transition(Status.READY,attempt=attempt)
                        return
                    transition(Status.RECOVERING if number <= self.budget.limits.recovery_retries else Status.VERIFYING,
                               attempt=attempt)
                    if number > self.budget.limits.recovery_retries:
                        raise PipelineError("Independent verification failed after the configured recovery limit")
                    failure = artifacts.sanitize({"tests":tests.model_dump(),"review":review.model_dump(),"attempt":number})
                    hosted = None
                    readback_error = 'Neatlogs readback is not configured'
                    if self.trace_reader and self.trace_reader.configured and attempt_trace:
                        from backend.integrations.neatlogs_read import ReadbackUnavailable
                        try:
                            if not self.telemetry.flush():
                                raise ReadbackUnavailable('Neatlogs attempt flush failed')
                            hosted = self.trace_reader.read(attempt_trace, check, expected_name=attempt_name)
                            if not any(str(s['status']).upper() in {'ERROR','FAILED','FAILURE'} for s in hosted['spans']):
                                raise ReadbackUnavailable('Neatlogs attempt does not contain the test failure')
                            save(f'failed-trace-{number}', hosted)
                        except ReadbackUnavailable as exc:
                            hosted = None
                            readback_error = str(exc)
                    evidence_source = 'neatlogs-public-api+local-artifacts' if hosted else 'local-artifacts'
                    result['recovery_evidence_source'] = evidence_source
                    with self.span('recovery-hosted-evidence' if hosted else 'recovery-local-evidence','AGENT',attempt=number):
                        strategy = recovery.recover(self.implementer_provider,plan,failure,changed,hosted,self.recipe,
                                                    patch=patch)
                    save(f"recovery-{number}",{"strategy":strategy,"evidence_source":evidence_source,
                                             'failed_trace_id':attempt_trace, 'readback_error':None if hosted else readback_error})
            except PipelineError as exc:
                # Lease/cancellation errors deliberately propagate to the worker.
                result["budget"] = self.budget.snapshot()
                if root_span is not None:
                    from opentelemetry.trace import Status as SpanStatus, StatusCode
                    root_span.set_status(SpanStatus(StatusCode.ERROR,str(exc)))
                    root_span.set_attribute("torque.status","failed")
                save("failure",{"error":str(exc),"result":result})
                checkpoint()
                store.update(run_id,owner,Status.FAILED,error=str(exc),result=artifacts.sanitize(result))
