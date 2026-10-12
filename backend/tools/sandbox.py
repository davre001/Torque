"""Docker-only execution. There is deliberately no host shell fallback."""
import os
import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import uuid
from backend.models import PipelineError, TestResult

class DockerRunner:
    def __init__(self, recipe):
        self.recipe = recipe
        self.suite_sha256 = None

    def preflight(self):
        if self.recipe.image == "remote-managed":
            raise PipelineError("This recipe requires TORQUE_RUNNER=github-actions")
        if not shutil.which("docker"):
            raise PipelineError("Docker is unavailable; install/start Docker before agent execution")
        suite = Path(self.recipe.suite_directory).resolve()
        if not suite.is_dir() or suite.is_symlink():
            raise PipelineError("Independent acceptance suite directory is unavailable")
        digest, total = hashlib.sha256(),0
        for file in sorted(suite.rglob("*")):
            if file.is_symlink():
                raise PipelineError("Acceptance suite symlinks are unsupported")
            if file.is_file():
                total += file.stat().st_size
                if total > 5_000_000:
                    raise PipelineError("Acceptance suite exceeds size limit")
                digest.update(str(file.relative_to(suite)).encode()+b"\0"+file.read_bytes())
        signature = digest.hexdigest()
        reporting = Path(__file__).resolve().parents[2]/'tests/acceptance/torque_reporting.py'
        signature = hashlib.sha256((signature+'\0').encode()+reporting.read_bytes()).hexdigest()
        if self.suite_sha256 is not None and signature != self.suite_sha256:
            raise PipelineError("Independent acceptance suite changed during the run")
        self.suite_sha256 = signature
        environment = {key:value for key,value in os.environ.items()
                       if key.upper() in {"PATH","SYSTEMROOT","WINDIR","TEMP","TMP","HOME","USERPROFILE","DOCKER_HOST","DOCKER_CONTEXT"}}
        try:
            check = subprocess.run(["docker","image","inspect",self.recipe.image],
                                   env=environment,capture_output=True,timeout=15)
        except (OSError,subprocess.TimeoutExpired) as exc:
            raise PipelineError("Docker daemon unavailable") from exc
        if check.returncode:
            raise PipelineError("Reviewed test image is not installed locally; automatic pulls are disabled")
        return suite,environment

    def run(self, workspace, checkpoint):
        suite,environment = self.preflight()
        workspace = Path(workspace).resolve()
        if suite.is_relative_to(workspace) or workspace.is_relative_to(suite):
            raise PipelineError("Acceptance tests must live outside the agent workspace")
        if "," in str(workspace) or "," in str(suite):
            raise PipelineError("Docker mount paths containing commas are unsupported")
        name = "torque-"+uuid.uuid4().hex
        security_args = []
        profile = suite/"seccomp_profile.json"
        if profile.is_file():
            security_args = ["--security-opt",f"seccomp={profile}"]
        args = ["docker","run","--rm","--init","--pull=never","--name",name,
                "--network=none","--read-only","--cap-drop=ALL",
                "--security-opt=no-new-privileges","--user","65534:65534",
                "--cpus=1","--memory=1g","--memory-swap=1g","--pids-limit=128",
                "--tmpfs","/tmp:rw,nosuid,nodev,size=256m",
                "--mount",f"type=bind,src={workspace},dst=/workspace,readonly",
                "--mount",f"type=bind,src={suite},dst=/acceptance,readonly",
                "--mount",f"type=bind,src={Path(__file__).resolve().parents[2]/'tests/acceptance/torque_reporting.py'},dst=/torque_reporting.py,readonly",
                "--workdir","/workspace",*security_args,self.recipe.image,*self.recipe.command]
        checkpoint()
        # Disk-backed output avoids unbounded Python memory; enforce a log cap.
        with tempfile.TemporaryFile() as output:
            try:
                process = subprocess.Popen(args,env=environment,stdout=output,stderr=subprocess.STDOUT)
            except OSError as exc:
                raise PipelineError("Unable to start Docker runner") from exc
            deadline = time.monotonic()+self.recipe.timeout_seconds
            timed_out = False
            try:
                while process.poll() is None:
                    checkpoint()
                    if time.monotonic() >= deadline or os.fstat(output.fileno()).st_size > 100000:
                        timed_out = True
                        break
                    time.sleep(.1)
            finally:
                if process.poll() is None:
                    subprocess.run(["docker","rm","-f",name],env=environment,
                                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
                    process.kill()
                process.wait(timeout=10)
            output.seek(0)
            text = output.read(100000).decode("utf-8",errors="replace")
        failure_kind,passed,cases = "infrastructure",0,[]
        for line in text.splitlines():
            if line.startswith("TORQUE_TEST_RESULT="):
                try:
                    report = json.loads(line.split("=",1)[1])
                    passed = int(report["assertions_passed"])
                    failure_kind = report["failure_kind"]
                    from backend.models import TestCaseResult
                    cases = [TestCaseResult.model_validate(case) for case in report.get('cases', [])]
                    if len(cases)>12 or (cases and sum(case.passed for case in cases)!=passed):
                        raise ValueError()
                    if failure_kind not in {None,"assertion","infrastructure"} or passed < 0:
                        raise ValueError()
                except (ValueError,KeyError,TypeError):
                    failure_kind,passed,cases = "infrastructure",0,[]
        if timed_out:
            failure_kind = "timeout"
        if process.returncode == 0 and passed != len(self.recipe.acceptance_criteria):
            failure_kind = "infrastructure"
        return TestResult(exit_code=process.returncode if not timed_out else 124,
                          output=text,timed_out=timed_out,command=self.recipe.command,
                          failure_kind=failure_kind,assertions_passed=passed,cases=cases)
