import pytest
from backend.integrations.providers import parse_response
from backend.models import PipelineError, Recovery


@pytest.mark.parametrize("text",['{"strategy":"fix"}',
    '```json\n{"strategy":"fix"}\n```','```\n{"strategy":"fix"}\n```',
    'I propose this fix.\n```json\n{"strategy":"fix"}\n```'])
def test_one_json_document_can_have_markdown_fences(text):
    assert parse_response(text,Recovery).strategy == "fix"


@pytest.mark.parametrize("text",['Here is the answer: {"strategy":"fix"}',
    '```json\n{"strategy":"fix"}\n```\nextra text','{"strategy":"fix","extra":"secret-value"}'])
def test_extra_prose_or_schema_fields_still_fail_without_exposing_input(text):
    with pytest.raises(PipelineError) as caught:
        parse_response(text,Recovery)
    assert "secret-value" not in str(caught.value)
