"""Controlled live recovery drill; no GitHub writes and no production queue changes.

The first patch is deliberately incorrect. All subsequent reasoning is live,
and acceptance executes in a separate Python process without executing model code.
"""
import hashlib
import json
import logging
import subprocess
import sys
import time
import uuid
from backend.artifacts import Artifacts
from backend.config import ROOT, Settings
from backend.execution import Limits, Recipe
from backend.integrations.gemini import Gemini
from backend.integrations.litellm import LiteLLM
from backend.integrations.neatlogs import Telemetry
from backend.integrations.neatlogs_read import TraceReader, ReadbackUnavailable
from backend.integrations.providers import Budget, StructuredProvider
from backend.models import Edit, Patch, PipelineError, TestResult, TestCaseResult
from backend.pipeline import Pipeline
from backend.runtime import SECRET_NAMES, rates
from backend.store import Store
from backend.worker import Worker

ACCEPTANCE = '''import ast, pathlib, sys
tree = ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert len(tree.body) == 1 and isinstance(tree.body[0], ast.Assign), "Expected one result assignment"
assert len(tree.body[0].targets) == 1 and isinstance(tree.body[0].targets[0], ast.Name) and tree.body[0].targets[0].id == "result", "Expected result assignment"
actual = ast.literal_eval(tree.body[0].value)
assert actual == 10, f"Expected result=10; actual={actual!r}"
print("PASS: result equals 10")
'''


class DemoGitHub:
    def issue(self, url):
        return {'title':'Controlled local recovery drill', 'body':'Set result to 10.', 'state':'open',
                'fixture':True, 'url':url}

    def revision(self, *args):
        return hashlib.sha1(b'result = 9\n').hexdigest()


class DemoRunner:
    def __init__(self, suite):
        self.suite=suite
        self.suite_sha256=hashlib.sha256(ACCEPTANCE.encode()).hexdigest()
        self.test_image='local-python-ast-assertion; no Docker image used'

    def preflight(self):
        pass

    def run(self, workspace, check):
        check()
        command=[sys.executable, str(self.suite), str(workspace/'app.py')]
        started=time.monotonic()
        result=subprocess.run(command,capture_output=True,text=True,timeout=10)
        check()
        return TestResult(exit_code=result.returncode,output=(result.stdout+result.stderr)[-4000:],
                          command=['python','independent-acceptance.py','app.py'],
                          failure_kind=None if result.returncode==0 else 'assertion',
                          assertions_passed=1 if result.returncode==0 else 0,
                          cases=[TestCaseResult(name='result-equals-10',passed=result.returncode==0,
                              duration_ms=(time.monotonic()-started)*1000,
                              stdout=result.stdout[-4000:],stderr=result.stderr[-4000:],
                              stacktrace=result.stderr[-6000:] if result.returncode else '')])


class SeededFirstPatch:
    def __init__(self, live):
        self.live=live
        self.seeded=False

    def ask(self, instructions, data, schema):
        if schema is Patch and not self.seeded:
            self.seeded=True
            return Patch(summary='Deliberately incorrect first patch for a controlled recovery drill',
                         edits=[Edit(path='app.py',original_sha256=data['current_files']['app.py']['sha256'],
                                     content='result = 8\n')])
        return self.live.ask(instructions,data,schema)


def main():
    Settings.load()
    if not __import__('os').getenv('NEATLOGS_TOKEN'):
        raise SystemExit('Save a service-account NEATLOGS_TOKEN in .env before running this drill.')
    import os
    secrets=tuple(os.getenv(name,'') for name in SECRET_NAMES)
    folder=ROOT/'var'/'recovery-demo'/uuid.uuid4().hex
    folder.mkdir(parents=True)
    suite=folder/'acceptance.py'
    suite.write_text(ACCEPTANCE,encoding='utf-8')
    telemetry=Telemetry(os.getenv('NEATLOGS_API_KEY',''),secrets)
    reader=TraceReader()
    clients=[]
    try:
        if not telemetry.active:
            raise PipelineError('Neatlogs ingest key is required for the live drill')
        # Check read authorization before any model spending.
        reader.get('project',lambda:None)
        limits=Limits(max_calls=6,max_tokens=30000,max_cost_usd=0.50,max_seconds=240,recovery_retries=1)
        budget=Budget(limits)
        gemini=Gemini(os.getenv('GEMINI_API_KEY',''),os.getenv('GEMINI_MODEL',''),telemetry.wrap)
        claude=LiteLLM(os.getenv('LITELLM_API_KEY',''),os.getenv('LITELLM_BASE_URL',''),os.getenv('LITELLM_MODEL',''),telemetry.wrap)
        clients=[gemini,claude]
        investigator=StructuredProvider(gemini,budget,*rates('GEMINI'),budget.check,transport_retries=0)
        implementer=StructuredProvider(claude,budget,*rates('LITELLM'),budget.check,transport_retries=0)
        store=Store(folder/'drill.sqlite3');store.initialize()
        run_id=store.submit('https://github.com/example/torque-recovery-fixture/issues/1')
        def prepare(owner,repo,sha,workspace,check):
            workspace.mkdir(parents=True)
            (workspace/'app.py').write_bytes(b'result = 9\n')
        recipe=Recipe(image='sha256:'+hashlib.sha256(ACCEPTANCE.encode()).hexdigest(),
                      command=['python','independent-acceptance.py','app.py'],context_files=['app.py'],
                      editable_files=['app.py'],acceptance_criteria=['result equals 10'],suite_directory=str(folder))
        pipeline=Pipeline(github=DemoGitHub(),prepare=prepare,runner=DemoRunner(suite),
                          investigator_provider=investigator,implementer_provider=SeededFirstPatch(implementer),
                          budget=budget,recipe=recipe,workspaces=folder/'workspaces',artifacts=folder/'artifacts',
                          telemetry=telemetry,trace_reader=reader,secrets=secrets)
        Worker(store,Settings(store.path),pipeline).once()
        run=store.get(run_id)
        if not telemetry.flush():
            raise PipelineError('Neatlogs final workflow flush failed')
        if not run['result'].get('verified') or [a['tests_passed'] for a in run['attempts']] != [False,True]:
            raise PipelineError('Live recovery drill did not verify; inspect '+str(folder))
        if run['result']['recovery_evidence_source'] != 'neatlogs-public-api+local-artifacts':
            raise PipelineError('Recovery used local fallback; hosted demonstration remains incomplete')
        finalized=reader.read(run['result']['trace_id'],expected_name='github-issue-to-pr')
        destination=ROOT/'evidence'/'recovery'/run_id
        exported=Artifacts(destination,secrets)
        records=[]
        for file in sorted((folder/'artifacts'/run_id).glob('*.json')):
            records.append(exported.write(file.stem,json.loads(file.read_text(encoding='utf-8'))))
        # Command paths and local fixtures are explicitly labeled, never represented as Docker or GitHub execution.
        run['result']['test_image']='local-python-ast-assertion; no Docker image used'
        records.append(exported.write('run',run))
        records.append(exported.write('workflow-readback',finalized))
        exported.write('manifest',{'mode':'controlled-live-recovery-drill','first_failure':'deliberately seeded incorrect patch',
                                  'github':'local metadata fixture; no GitHub requests or PR publication',
                                  'acceptance':'independent subprocess AST assertion; model code never executed',
                                  'records':records})
        (destination/'README.md').write_text(
            '# Controlled live recovery evidence\n\n'
            'This is a controlled local drill, not the kokon production demo. The first patch was deliberately incorrect. '
            'The independent subprocess failed, Neatlogs finalized and returned that exact failed attempt, '
            'and live Claude recovery/implementation repaired it. The unchanged assertion then passed and live Gemini reviewed it. '
            'No GitHub calls, PR writes, or Docker execution occurred.\n\n'
            f'Run: `{run_id}`. Main trace: `{run["result"]["trace_id"]}`.\n'
            f'Estimated model cost: ${budget.estimated_cost:.6f}. See the manifest and readback records.\n',encoding='utf-8')
        print(json.dumps({'status':'verified-hosted-recovery','run_id':run_id,'evidence':str(destination),
                          'trace_id':run['result']['trace_id'],'budget':budget.snapshot()},indent=2))
    except (PipelineError,ReadbackUnavailable) as exc:
        raise SystemExit(str(exc)) from None
    finally:
        for client in clients:client.close()
        reader.close();telemetry.close()


if __name__=='__main__':
    logging.basicConfig(level=logging.WARNING)
    main()
