"""No-model/no-GitHub forced-failure probe for acceptance diagnostics."""
import json
import os
from pathlib import Path
import tempfile
import uuid
from opentelemetry.trace import Status, StatusCode
from backend.artifacts import Artifacts
from backend.config import ROOT, Settings
from backend.integrations.neatlogs import Telemetry
from backend.integrations.neatlogs_read import TraceReader, ReadbackUnavailable
from backend.integrations.test_diagnostics import trace_test_result
from backend.integrations.neatlogs_mcp import NeatlogsMCP
from backend.recovery_demo import ACCEPTANCE, DemoRunner
from backend.runtime import SECRET_NAMES


def main():
    Settings.load()
    secrets=tuple(os.getenv(name,'') for name in SECRET_NAMES)
    telemetry=Telemetry(os.getenv('NEATLOGS_API_KEY',''),secrets)
    reader=TraceReader()
    if not telemetry.active or not reader.configured:
        raise SystemExit('Neatlogs ingest and readback credentials are required')
    output=ROOT/'evidence/acceptance-telemetry'/uuid.uuid4().hex
    artifacts=Artifacts(output,secrets)
    mcp=None
    try:
        reader.get('project',lambda:None)
        mcp=NeatlogsMCP()
        mcp.call('ping',{});mcp.call('whoami',{})
        records=[]
        with tempfile.TemporaryDirectory(prefix='torque-telemetry-') as temporary:
            workspace=Path(temporary)
            suite=workspace/'acceptance.py';suite.write_text(ACCEPTANCE,encoding='utf-8')
            for value in (8,10):
                name='acceptance-diagnostics-forced-failure' if value==8 else 'acceptance-diagnostics-passing-check'
                (workspace/'app.py').write_text(f'result = {value}\n',encoding='utf-8')
                with telemetry.attempt(name,controlled_probe=True) as root:
                    result=DemoRunner(suite).run(workspace,lambda:None)
                    trace_test_result(telemetry,result)
                    root.set_status(Status(StatusCode.OK if result.passed else StatusCode.ERROR,
                                           None if result.passed else 'Controlled independent assertion failed'))
                trace_id=format(root.get_span_context().trace_id,'032x')
                if not telemetry.flush():raise ReadbackUnavailable('Trace flush failed')
                summary=reader.read(trace_id,expected_name=name)
                artifacts.write('failure-readback' if value==8 else 'passing-readback',summary)
                context=mcp.call('get_trace_context',{'trace_id':trace_id})
                if not context.get('verification_ready') or not context.get('span_payload_complete'):
                    raise ReadbackUnavailable('Hosted MCP trace payload is incomplete')
                children=[s for s in context.get('spans',[]) if s.get('name')=='acceptance-test-case']
                if len(children)!=1:raise ReadbackUnavailable('Expected one hosted per-test child')
                expected_statuses={'ERROR'} if value==8 else {'OK','SUCCESS'}
                if str(children[0].get('status')).upper() not in expected_statuses:
                    raise ReadbackUnavailable('Hosted test status does not match assertion result')
                attrs=children[0].get('output_value',{})
                if isinstance(attrs,str):
                    try:attrs=json.loads(attrs)
                    except ValueError:raise ReadbackUnavailable('Hosted diagnostics are malformed') from None
                if not isinstance(attrs,dict):raise ReadbackUnavailable('Hosted child attributes unavailable')
                safe=artifacts.sanitize({k:v for k,v in attrs.items() if k.startswith('test.')})
                if safe.get('test.name')!='result-equals-10':
                    raise ReadbackUnavailable('Hosted test identity unavailable')
                if value==8 and not ('AssertionError' in safe.get('test.stacktrace','') and
                                     'actual=8' in safe.get('test.stderr','')):
                    raise ReadbackUnavailable('Hosted failure stacktrace or stderr unavailable')
                artifacts.write('failure' if value==8 else 'passing',{'trace':summary,'diagnostics':safe})
                records.append({'trace_id':trace_id,'passed':result.passed})
        artifacts.write('manifest',{'mode':'controlled-acceptance-instrumentation-probe',
            'models_used':False,'github_writes':False,'records':records})
        print(json.dumps({'status':'verified-hosted-test-diagnostics','evidence':str(output),'records':records},indent=2))
    except ReadbackUnavailable as exc:
        raise SystemExit(str(exc)) from None
    finally:
        if mcp:mcp.close()
        reader.close();telemetry.close()


if __name__=='__main__':main()
