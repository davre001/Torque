"""GitHub workflow entry point. Only public demo source enters the test container."""
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from backend.config import ROOT
from backend.execution import Recipe
from backend.models import TestResult
from backend.tools.repository import snapshot
from backend.tools.files import safe_path
from backend.tools.sandbox import DockerRunner

def main():
    request_id = os.environ["TORQUE_REQUEST_ID"]
    sha = os.environ["TORQUE_SOURCE_SHA"]
    if not re.fullmatch("[a-f0-9]{32}",request_id) or not re.fullmatch("[a-f0-9]{40}",sha):
        raise ValueError("Invalid request identity")
    record = {"request_id":request_id,"source_sha":sha,"suite_sha256":None}
    try:
        encoded = os.environ["TORQUE_INDEX_HTML"]
        if len(encoded) > 60000:
            raise ValueError("Oversized input")
        replacement = base64.b64decode(encoded,validate=True).decode("utf-8")
        # No inputs are interpolated into shell commands.
        subprocess.run(["docker","build","-t","torque-kokon-tests",
                        str(ROOT/"tests"/"acceptance"/"kokon")],check=True,timeout=300)
        image = subprocess.check_output(["docker","image","inspect","torque-kokon-tests",
                                         "--format","{{.Id}}"],text=True).strip()
        record["image_digest"] = image
        recipe = Recipe(image=image,command=["python","/acceptance/test_reduced_motion.py"],
                        context_files=["site/index.html"],editable_files=["site/index.html"],
                        acceptance_criteria=["reduced motion paused","manual play","normal autoplay"],
                        suite_directory=str(ROOT/"tests"/"acceptance"/"kokon"))
        runner = DockerRunner(recipe)
        runner.preflight()
        record["suite_sha256"] = runner.suite_sha256
        with tempfile.TemporaryDirectory(prefix="torque-source-") as temporary:
            workspace = Path(temporary)/"source"
            snapshot("GabrieleLozupone","kokon",sha,workspace,lambda:None)
            safe_path(workspace,"site/index.html").write_bytes(replacement.encode())
            result = runner.run(workspace,lambda:None)
        record["result"] = result.model_dump()
    except Exception:
        # Do not export exception text or workflow environment.
        record["result"] = TestResult(exit_code=125,output="Remote runner infrastructure failed",
            failure_kind="infrastructure",command=["remote-kokon-acceptance"]).model_dump()
    Path("remote-result").mkdir(exist_ok=True)
    Path("remote-result/result.json").write_text(json.dumps(record),encoding="utf-8")

if __name__ == "__main__":
    main()
