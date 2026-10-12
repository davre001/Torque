import importlib.util
from pathlib import Path
import pytest
from backend.integrations.test_diagnostics import trace_test_result
from backend.recovery_demo import DemoRunner, ACCEPTANCE
from test_hosted_recovery import instrument


def test_forced_subprocess_failure_has_named_child_stack_and_redacted_output(tmp_path, monkeypatch):
    suite=tmp_path/'acceptance.py'
    suite.write_text(ACCEPTANCE)
    (tmp_path/'app.py').write_text('result = 8\n')
    telemetry, exporter=instrument(monkeypatch)
    telemetry.redactor.secrets=('sensitive-token',)
    with telemetry.attempt('forced-acceptance-failure') as root:
        result=DemoRunner(suite).run(tmp_path, lambda:None)
        assert not result.passed
        result.cases[0].stderr+=' sensitive-token'
        trace_test_result(telemetry,result)
    spans=exporter.get_finished_spans()
    child=next(s for s in spans if s.name=='acceptance-test-case')
    assert child.parent.span_id==root.get_span_context().span_id
    assert child.status.status_code.name=='ERROR'
    assert child.attributes['test.name']=='result-equals-10'
    assert 'AssertionError: Expected result=10; actual=8' in child.attributes['test.stacktrace']
    assert 'Traceback' in child.attributes['test.stderr']
    assert 'sensitive-token' not in child.attributes['test.stderr']
    assert child.attributes['test.execution_duration_ms']>0
    import json
    exported=json.loads(child.attributes['neatlogs.tool.output'])
    assert exported['test.name']=='result-equals-10'
    assert 'AssertionError' in exported['test.stacktrace']
    assert 'sensitive-token' not in child.attributes['neatlogs.tool.output']
    (tmp_path/'app.py').write_text('result = 10\n')
    with telemetry.attempt('passing-acceptance'):
        passed=DemoRunner(suite).run(tmp_path,lambda:None)
        trace_test_result(telemetry,passed)
    assert passed.passed
    assert exporter.get_finished_spans()[-2].status.status_code.name=='OK'


def test_reporting_preserves_exception_and_captures_bounded_streams():
    file=Path(__file__).parent/'acceptance/torque_reporting.py'
    spec=importlib.util.spec_from_file_location('reporting',file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    reporter=module.Reporter()
    with pytest.raises(AssertionError,match='forced'):
        with reporter.case('forced-check'):
            print('a'*10000)
            raise AssertionError('forced')
    case=reporter.cases[0]
    assert not case['passed']
    assert len(case['stdout'])==4000
    assert 'AssertionError: forced' in case['stacktrace']
