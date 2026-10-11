from types import SimpleNamespace
import pytest
import backend.runtime as runtime
from backend.models import PipelineError


def test_claude_trial_uses_paid_rates_for_every_role_and_closes_once(monkeypatch):
    monkeypatch.setenv('TORQUE_PROVIDER_MODE', 'claude-only')
    monkeypatch.setenv('NEATLOGS_API_KEY', 'fixture')
    monkeypatch.setenv('LITELLM_INPUT_USD_PER_MILLION', '3')
    monkeypatch.setenv('LITELLM_OUTPUT_USD_PER_MILLION', '15')
    monkeypatch.delenv('GEMINI_INPUT_USD_PER_MILLION', raising=False)
    monkeypatch.setenv('TORQUE_RUNNER', 'docker')
    closed = []
    claude = SimpleNamespace(close=lambda: closed.append('claude'))
    client = SimpleNamespace(close=lambda: None)
    monkeypatch.setattr(runtime, 'LiteLLM', lambda *args: claude)
    def forbidden(*args):
        pytest.fail('Claude-only mode must not construct Gemini')
    monkeypatch.setattr(runtime, 'Gemini', forbidden)
    monkeypatch.setattr(runtime, 'GitHub', lambda *args: client)
    import backend.integrations.neatlogs_read as readback
    monkeypatch.setattr(readback, 'TraceReader', lambda: client)
    monkeypatch.setattr(runtime, 'DockerRunner', lambda recipe: SimpleNamespace(preflight=lambda: None))
    monkeypatch.setattr(runtime, 'load_recipes', lambda: {'davre001/kokon': object()})
    def pipeline(**kwargs):
        reasoning = kwargs['investigator_provider']
        edits = kwargs['implementer_provider']
        assert reasoning.adapter is edits.adapter is claude
        assert reasoning.rates == edits.rates == (3., 15.)
        assert reasoning.budget is edits.budget
        return lambda *args: None
    monkeypatch.setattr(runtime, 'Pipeline', pipeline)
    processor = object.__new__(runtime.AgentProcessor)
    processor.secrets = ()
    processor.telemetry = SimpleNamespace(wrap=lambda c: c, redactor=SimpleNamespace(secrets=()))
    store = SimpleNamespace(get=lambda _: {'issue_url': 'https://github.com/davre001/kokon/issues/2', 'user_id': 'operator'})
    processor(store, 'fixture', 'owner', lambda: None)
    assert closed == ['claude']


def test_unknown_provider_mode_fails_closed(monkeypatch):
    monkeypatch.setenv('TORQUE_PROVIDER_MODE', 'automatic-fallback')
    with pytest.raises(PipelineError, match='TORQUE_PROVIDER_MODE'):
        runtime.provider_mode()
