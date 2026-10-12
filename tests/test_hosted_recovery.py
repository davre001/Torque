from contextlib import contextmanager
import json
import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from backend.integrations.neatlogs import Telemetry
from backend.integrations.neatlogs_read import ReadbackUnavailable
from backend.models import Recovery
from test_pipeline import FixtureModels, pipeline_run


def instrument(monkeypatch):
    exporter=InMemorySpanExporter()
    provider=TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer=provider.get_tracer('recovery-test')
    @contextmanager
    def trace(name,kind,**attributes):
        with tracer.start_as_current_span(name,attributes=attributes) as span:
            yield span
    monkeypatch.setattr('neatlogs.trace',trace)
    monkeypatch.setattr('neatlogs.flush',lambda **kwargs:True)
    telemetry=Telemetry('',())
    telemetry.active=True
    return telemetry,exporter


@pytest.mark.parametrize('mode',['hosted','unavailable','wrong-status'])
def test_recovery_uses_only_verified_failed_trace_and_restores_parent(tmp_path,monkeypatch,mode):
    telemetry,exporter=instrument(monkeypatch)
    class Reader:
        configured=True
        def read(self,trace_id,check,expected_name):
            check()
            if mode=='unavailable':raise ReadbackUnavailable('Neatlogs readback HTTP 403')
            closed=[s for s in exporter.get_finished_spans() if format(s.context.trace_id,'032x')==trace_id]
            assert len(closed)==2
            root=next(s for s in closed if s.parent is None)
            child=next(s for s in closed if s.parent is not None)
            assert child.parent.span_id==root.context.span_id
            assert child.name=='acceptance-runner-diagnostics'
            assert root.name==expected_name
            assert root.status.status_code.name=='ERROR'
            return {'trace_id':trace_id,'finalization_status':'finalized',
                    'spans':[{'spanName':expected_name,'status':'ERROR' if mode=='hosted' else 'OK'}]}
    class Models(FixtureModels):
        def ask(self,instructions,data,schema):
            if schema is Recovery:
                self.recoveries+=1
                assert bool(data['hosted_trace'])==(mode=='hosted')
                assert data['evidence_source'].startswith('neatlogs-public-api' if mode=='hosted' else 'local-artifacts')
                return Recovery(strategy='Set the result to fixed')
            return super().ask(instructions,data,schema)
    store,rid,models=pipeline_run(tmp_path,Models(),telemetry,Reader())
    run=store.get(rid)
    assert run['result']['verified']
    expected='neatlogs-public-api+local-artifacts' if mode=='hosted' else 'local-artifacts'
    assert run['result']['recovery_evidence_source']==expected
    record=json.loads((tmp_path/'artifacts'/rid/'recovery-1.json').read_text())
    assert record['evidence_source']==expected
    assert bool(record['readback_error'])==(mode!='hosted')
    finished=exporter.get_finished_spans()
    main=next(s for s in finished if s.name=='github-issue-to-pr')
    recovery=next(s for s in finished if s.name.startswith('recovery-'))
    assert main.context.trace_id==recovery.context.trace_id
    assert main.context.trace_id!=int(run['attempts'][0]['test_trace_id'],16)
    assert [a['tests_passed'] for a in run['attempts']]==[False,True]
