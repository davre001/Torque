from types import SimpleNamespace
from backend.integrations.litellm import LiteLLM


def test_gateway_requests_json_without_changing_model_or_output_limit():
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok":true}'))],
            usage=SimpleNamespace(prompt_tokens=10,completion_tokens=5))
    adapter = LiteLLM.__new__(LiteLLM)
    adapter.model = "fixture-claude"
    adapter.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    result = adapter.complete("JSON task",512)
    assert calls[0]["response_format"] == {"type":"json_object"}
    assert calls[0]["messages"][0]["role"] == "system"
    assert calls[0]["messages"][1]["content"] == "JSON task"
    assert calls[0]["max_tokens"] == 512
    assert result.input_tokens == 10
