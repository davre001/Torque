import hashlib
import pytest
from backend.models import Edit, Patch, PipelineError, Replacement
from backend.tools.patches import apply_patch


def test_small_replacement_preserves_large_file(tmp_path):
    original = "unchanged\n" * 3000 + "play();\n"
    path = tmp_path/"index.html"
    path.write_bytes(original.encode())
    patch = Patch(summary="Respect motion preference",edits=[Edit(
        path="index.html",original_sha256=hashlib.sha256(original.encode()).hexdigest(),
        replacements=[Replacement(search="play();",replacement="if (!reducedMotion) play();")])])
    apply_patch(tmp_path,patch,["index.html"])
    assert path.read_bytes() == original.replace("play();","if (!reducedMotion) play();").encode()


@pytest.mark.parametrize("search",["missing","same"])
def test_missing_or_ambiguous_replacement_changes_nothing(tmp_path,search):
    original = b"same same"
    path = tmp_path/"index.html"
    path.write_bytes(original)
    patch = Patch(summary="Fix",edits=[Edit(path="index.html",
        original_sha256=hashlib.sha256(original).hexdigest(),replacements=[
            Replacement(search=search,replacement="new")])])
    with pytest.raises(PipelineError,match="exactly once"):
        apply_patch(tmp_path,patch,["index.html"])
    assert path.read_bytes() == original


def test_replacement_validation_remains_atomic_across_files(tmp_path):
    edits = []
    for name in ("one.html","two.html"):
        (tmp_path/name).write_bytes(b"original")
        edits.append(Edit(path=name,original_sha256=hashlib.sha256(b"original").hexdigest(),
            replacements=[Replacement(search="original" if name == "one.html" else "missing",replacement="new")]))
    with pytest.raises(PipelineError):
        apply_patch(tmp_path,Patch(summary="Fix",edits=edits),["one.html","two.html"])
    assert all((tmp_path/name).read_bytes() == b"original" for name in ("one.html","two.html"))
