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
import zlib
import httpx
from backend.models import PipelineError, TestResult
from backend.tools.files import read_files

class ActionsRunner:
    def __init__(self, recipe, client=None, clock=time.monotonic, pause=time.sleep):
        self.recipe = recipe
        self.repository = os.getenv("TORQUE_ACTIONS_REPOSITORY","davre001/Torque")
        self.ref = os.getenv("TORQUE_ACTIONS_REF","torque-runner-v1")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",self.repository):
            raise PipelineError("Invalid Actions repository")
        self.token = os.getenv("TORQUE_ACTIONS_TOKEN","")
        self.workflow = "torque-remote-tests.yml"
        self.client = client or httpx.Client(base_url="https://api.github.com",timeout=20,
            headers={"Authorization":"Bearer "+self.token,"Accept":"application/vnd.github+json",
                     "X-GitHub-Api-Version":"2026-03-10"},follow_redirects=False)
        self.clock,self.pause = clock,pause
        self.source = None
        self.source_repository = None
        from backend.acceptance_profiles import profile_for
        try:self.profile = profile_for(recipe)
        except ValueError:self.profile = None
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
        if self.profile in {'gallery-keyboard','slider-keyboard'}:
            workflow=self._request('GET',f'/repos/{self.repository}/contents/.github/workflows/{self.workflow}',params={'ref':sha}).json()
            try:
                if workflow.get('encoding')!='base64' or workflow.get('size',0)>20000:raise ValueError()
                contents=base64.b64decode(workflow['content']).decode()
                if self.profile=='slider-keyboard' and 'slider-keyboard' not in contents: raise ValueError()
                if not all(marker in contents for marker in ('files_bundle:','acceptance_profile:','TORQUE_FILES_BUNDLE','TORQUE_ACCEPTANCE_PROFILE')):raise ValueError()
            except (KeyError,ValueError,UnicodeError):
                raise PipelineError('Push the gallery-capable workflow before submitting gallery runs') from None

    def bind_source(self,owner,repo,sha):
        repository = f"{owner}/{repo}".lower()
        if repository not in {"gabrielelozupone/kokon", "davre001/kokon"} or not re.fullmatch("[a-f0-9]{40}",sha):
            raise PipelineError("The first remote runner supports only the pinned public kokon demo")
        from backend.acceptance_profiles import profile_for, validate_source
        try:self.profile=profile_for(self.recipe)
        except ValueError:raise PipelineError('Remote kokon recipe exceeds reviewed scope') from None
        if not validate_source(self.profile,repository,sha):
            raise PipelineError(f'The repository revision is not reviewed for the {self.profile} test profile; update the operator-reviewed recipe and source revision')
        self.source = sha
        self.source_repository = repository

    def run(self,workspace,checkpoint):
        self.preflight()
        if self.source is None:
            raise PipelineError("Remote runner source has not been pinned")
        if self.profile in {'gallery-keyboard','slider-keyboard'}:
            files=read_files(Path(workspace),self.recipe.editable_files)
            raw=json.dumps({name:item['content'] for name,item in files.items()}).encode()
            if len(raw)>250000:raise PipelineError('Gallery source bundle exceeds decoded input limit')
            bundle=base64.b64encode(zlib.compress(raw)).decode()
            inputs={'request_id':None,'source_sha':self.source,'index_html':'',
                    'source_repository':self.source_repository,'acceptance_profile':self.profile,'files_bundle':bundle}
        else:
            content = read_files(Path(workspace),["site/index.html"])["site/index.html"]["content"]
            bundle = base64.b64encode(content.encode()).decode()
            inputs={'request_id':None,'source_sha':self.source,'index_html':bundle}
        # workflow_dispatch has a limited input payload; never truncate source.
        if len(bundle) > 60000:
            raise PipelineError("Remote demo patch exceeds the workflow input size limit")
        request_id = uuid.uuid4().hex
        inputs['request_id']=request_id
        checkpoint()
        self._request("POST",f"/repos/{self.repository}/actions/workflows/{self.workflow}/dispatches",
            json={"ref":self.ref,"inputs":inputs})
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
        if self.profile in {'gallery-keyboard','slider-keyboard','repository-tests'} and (record.get('acceptance_profile')!=self.profile or record.get('source_repository')!=self.source_repository):
            raise PipelineError('Remote test profile/source does not match request')
        remote_result = TestResult.model_validate(record['result'])
        if remote_result.failure_kind == 'infrastructure' and not record.get('suite_sha256'):
            # A failed preparation cannot certify a suite or a passing result.
            # Request, repository, profile and workflow identity still apply.
            if remote_result.exit_code == 0 or remote_result.assertions_passed:
                raise PipelineError('Invalid infrastructure failure result')
            return remote_result
        signature = record["suite_sha256"]
        if self.profile == 'repository-tests' and (record.get('suite_revision') != self.suite_sha or not re.fullmatch('[a-f0-9]{64}', signature or '')):
            raise PipelineError('Frozen repository tests do not match setup')
        if self.suite_sha256 is not None and signature != self.suite_sha256:
            raise PipelineError("Remote acceptance suite changed between attempts")
        self.suite_sha256 = signature
        self.test_image = record.get("image_digest")
        return TestResult.model_validate(record["result"])

    def close(self):
        self.client.close()
