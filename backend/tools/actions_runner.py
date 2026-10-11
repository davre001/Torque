"""GitHub-hosted Linux execution for the public kokon demo, with no local Docker."""
import base64
import io
import json
import os
from pathlib import Path
import re
import time
import uuid
import zipfile
import httpx
from backend.models import PipelineError, TestResult
from backend.tools.files import read_files

class ActionsRunner:
    def __init__(self, recipe, client=None, clock=time.monotonic, pause=time.sleep):
        self.recipe = recipe
        self.repository = os.getenv("TORQUE_ACTIONS_REPOSITORY","davre001/Torque")
        self.ref = os.getenv("TORQUE_ACTIONS_REF","main")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",self.repository):
            raise PipelineError("Invalid Actions repository")
        self.token = os.getenv("TORQUE_ACTIONS_TOKEN","")
        self.workflow = "torque-remote-tests.yml"
        self.client = client or httpx.Client(base_url="https://api.github.com",timeout=20,
            headers={"Authorization":"Bearer "+self.token,"Accept":"application/vnd.github+json",
                     "X-GitHub-Api-Version":"2026-03-10"},follow_redirects=False)
        self.clock,self.pause = clock,pause
        self.source = None
        self.suite_sha256 = None
        self.workflow_sha = None
        self.test_image = None

    def _request(self,method,path,**kwargs):
        try:
            response = self.client.request(method,path,**kwargs)
            if response.status_code >= 400:
                response.raise_for_status()
            return response
        except httpx.HTTPError:
            raise PipelineError("GitHub Actions request failed; check token permissions and workflow availability") from None

    def preflight(self):
        if not self.token:
            raise PipelineError("Set TORQUE_ACTIONS_TOKEN with Actions read/write and Contents read on the runner repository")
        response = self._request("GET",f"/repos/{self.repository}/actions/workflows/{self.workflow}")
        if response.json().get("state") != "active":
            raise PipelineError("Remote test workflow is not active")
        from urllib.parse import quote
        sha = self._request("GET",f"/repos/{self.repository}/commits/{quote(self.ref,safe='')}").json()["sha"]
        if self.workflow_sha is not None and self.workflow_sha != sha:
            raise PipelineError("Runner workflow revision changed during this run")
        self.workflow_sha = sha

    def bind_source(self,owner,repo,sha):
        repository = f"{owner}/{repo}".lower()
        if repository not in {"gabrielelozupone/kokon", "davre001/kokon"} or not re.fullmatch("[a-f0-9]{40}",sha):
            raise PipelineError("The first remote runner supports only the pinned public kokon demo")
        # remote_job downloads upstream. The reviewed fork is valid only when its
        # complete source tree is the identical upstream commit, not just one file.
        if repository == "davre001/kokon" and sha != "995b078b79819c0049db3eef96fc6bd91b016b12":
            raise PipelineError("The reviewed demo fork must retain the verified upstream revision")
        if self.recipe.editable_files != ["site/index.html"] or len(self.recipe.acceptance_criteria) != 3:
            raise PipelineError("Remote kokon recipe must retain its one-file edit scope and three criteria")
        self.source = sha

    def run(self,workspace,checkpoint):
        self.preflight()
        if self.source is None:
            raise PipelineError("Remote runner source has not been pinned")
        content = read_files(Path(workspace),["site/index.html"])["site/index.html"]["content"]
        bundle = base64.b64encode(content.encode()).decode()
        # workflow_dispatch has a limited input payload; never truncate source.
        if len(bundle) > 60000:
            raise PipelineError("Remote demo patch exceeds the workflow input size limit")
        request_id = uuid.uuid4().hex
        checkpoint()
        self._request("POST",f"/repos/{self.repository}/actions/workflows/{self.workflow}/dispatches",
            json={"ref":self.ref,"inputs":{"request_id":request_id,"source_sha":self.source,"index_html":bundle}})
        deadline = self.clock()+600
        run = None
        try:
            while self.clock() < deadline:
                checkpoint()
                if run is None:
                    runs = self._request("GET",f"/repos/{self.repository}/actions/workflows/{self.workflow}/runs",
                        params={"event":"workflow_dispatch","per_page":100}).json()["workflow_runs"]
                    run = next((item for item in runs if item["display_title"]=="Torque test "+request_id),None)
                else:
                    run = self._request("GET",f"/repos/{self.repository}/actions/runs/{run['id']}").json()
                if run is not None:
                    if run["head_sha"] != self.workflow_sha:
                        raise PipelineError("Remote job ran a different workflow revision")
                    if run["status"] == "completed":
                        result = self._completed_result(run,request_id,checkpoint)
                        return result
                self.pause(3)
            raise PipelineError("Remote test job timed out")
        finally:
            if run and run["status"] != "completed":
                try:
                    self._request("POST",f"/repos/{self.repository}/actions/runs/{run['id']}/cancel")
                except PipelineError:
                    pass  # Server timeout still bounds the job if cancellation fails.

    def _completed_result(self, run, request_id, checkpoint):
        for attempt in range(2):
            checkpoint()
            try:
                return self._result(run, request_id)
            except httpx.HTTPError:
                if attempt:
                    raise PipelineError('Remote acceptance result download failed; check network access') from None
                self.pause(1)
            except (zipfile.BadZipFile, KeyError, ValueError):
                raise PipelineError('Remote acceptance result is malformed; verification stopped') from None

    def _result(self,run,request_id):
        artifacts = self._request("GET",f"/repos/{self.repository}/actions/runs/{run['id']}/artifacts").json()["artifacts"]
        artifact = next((a for a in artifacts if a["name"]=="torque-result-"+request_id),None)
        if artifact is None or artifact["size_in_bytes"] > 200000 or artifact["expired"]:
            raise PipelineError("Remote result artifact missing, expired, or oversized")
        redirect = self._request("GET",f"/repos/{self.repository}/actions/artifacts/{artifact['id']}/zip")
        url = redirect.headers.get("location","")
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith((".blob.core.windows.net",".githubusercontent.com")):
            raise PipelineError("Unexpected artifact download host")
        # Signed artifact URL is fetched without the GitHub bearer token.
        payload = bytearray()
        with httpx.stream("GET",url,timeout=30,follow_redirects=False) as response:
            response.raise_for_status()
            for chunk in response.iter_bytes():
                payload.extend(chunk)
                if len(payload) > 200000:
                    raise PipelineError("Remote result archive exceeds limit")
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            item = archive.getinfo("result.json")
            if item.file_size > 150000:
                raise PipelineError("Remote result exceeds limit")
            record = json.loads(archive.read(item))
        if record["request_id"] != request_id or record["source_sha"] != self.source:
            raise PipelineError("Remote result identity does not match request")
        signature = record["suite_sha256"]
        if self.suite_sha256 is not None and signature != self.suite_sha256:
            raise PipelineError("Remote acceptance suite changed between attempts")
        self.suite_sha256 = signature
        self.test_image = record.get("image_digest")
        return TestResult.model_validate(record["result"])

    def close(self):
        self.client.close()
