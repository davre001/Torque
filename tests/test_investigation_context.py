import pytest
from backend.models import PipelineError
from backend.tools.files import investigation_context


def test_excerpts_preserve_hash_and_original_context_and_merge_windows():
    lines = [f"unrelated {i}\n" for i in range(100)]
    lines[50] = "reel.play();\n"
    lines[53] = "reel.pause();\n"
    context = {"index.html":{"content":"".join(lines),"sha256":"a"*64}}
    result = investigation_context(context,{"index.html":["reel"]})
    assert result["index.html"]["sha256"] == "a"*64
    assert result["index.html"]["is_excerpt"] is True
    assert result["index.html"]["content"].count("reel.play();") == 1
    assert "original line 39" in result["index.html"]["content"]
    assert "unrelated 0\n" not in result["index.html"]["content"]
    assert context["index.html"]["content"] == "".join(lines)


def test_no_match_requires_recipe_review_instead_of_sending_full_file():
    with pytest.raises(PipelineError,match="did not match"):
        investigation_context({"index.html":{"content":"hello","sha256":"a"*64}},
                              {"index.html":["reel"]})


def test_selected_context_remains_bounded():
    with pytest.raises(PipelineError,match="size limit"):
        investigation_context({"index.html":{"content":"reel"*10000,"sha256":"a"*64}},
                              {"index.html":["reel"]})
