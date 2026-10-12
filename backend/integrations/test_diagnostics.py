"""Export reported checks as children of the active acceptance attempt.

Spans describe completed subprocess checks; their actual execution duration is
reported separately rather than representing export time as test execution time.
"""
from opentelemetry.trace import Status, StatusCode
import json


def trace_test_result(telemetry, result):
    if not telemetry:
        return
    for case in result.cases:
        # Keep span names stable; subprocess-provided names are redacted as attributes.
        with telemetry.span('acceptance-test-case', 'TOOL') as span:
            if span is None:
                continue
            span.set_attribute('test.name', telemetry.redactor.sanitize(case.name))
            span.set_attribute('test.passed', case.passed)
            span.set_attribute('test.execution_duration_ms', case.duration_ms)
            span.set_attribute('test.reporting_mode', 'completed-subprocess-check')
            if not case.passed:
                for key in ('stdout', 'stderr', 'stacktrace'):
                    span.set_attribute('test.'+key, telemetry.redactor.sanitize(getattr(case, key)))
            diagnostics={'test.name':case.name,'test.passed':case.passed,
                         'test.execution_duration_ms':case.duration_ms,
                         'test.reporting_mode':'completed-subprocess-check'}
            if not case.passed:
                diagnostics.update({'test.'+key:getattr(case,key) for key in ('stdout','stderr','stacktrace')})
            # The installed SDK serializes canonical tool output into the hosted
            # span payload; arbitrary OTel attributes alone are not exposed there.
            span.set_attribute('neatlogs.tool.output',json.dumps(telemetry.redactor.sanitize(diagnostics)))
            span.set_status(Status(StatusCode.OK if case.passed else StatusCode.ERROR,
                                   None if case.passed else 'Independent acceptance check failed'))
    if not result.cases:
        with telemetry.span('acceptance-runner-diagnostics', 'TOOL') as span:
            if span is not None:
                span.set_attribute('test.details_available', False)
                span.set_attribute('test.failure_kind', result.failure_kind or 'none')
                span.set_attribute('test.output', telemetry.redactor.sanitize(result.output[-4000:]))
                span.set_status(Status(StatusCode.OK if result.passed else StatusCode.ERROR))
