from types import SimpleNamespace
from backend.agents.verifier import verify
from backend.models import Plan,Review,TestResult as Result


def test_review_sees_all_diff_hunks_but_not_verbose_test_logs():
    before = "unrelated\n"*100 + "reel.play();\n"
    after = before.replace("unrelated\n","unrelated-change\n",1).replace("reel.play();","if (!reduce) reel.play();")
    calls = []
    class Provider:
        def ask(self,instructions,data,schema):
            calls.append(data)
            return Review(approved=True,rationale="fixture",satisfied_criteria=[0])
    plan = Plan(summary="Respect reduced motion",files=["index.html"],acceptance_criteria=["paused"])
    result = Result(exit_code=0,output="private verbose logs",command=["test"],assertions_passed=1)
    verify(Provider(),plan,{"index.html":{"content":after,"sha256":"a"*64}},result,
        recipe=SimpleNamespace(investigation_terms={"index.html":["reel"]}),originals={"index.html":before})
    assert "unrelated-change" in calls[0]["changes"]["index.html"]
    assert "if (!reduce) reel.play();" in calls[0]["changes"]["index.html"]
    assert "output" not in calls[0]["tests"]
    assert calls[0]["tests"]["assertions_passed"] == 1
    assert len(calls[0]["files"]["index.html"]["content"]) < len(after)
