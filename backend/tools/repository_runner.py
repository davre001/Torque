"""Managed repository tests; callers supply file scope, never host commands."""
import base64
import json
import os
import re
import uuid
import zlib
from pathlib import Path
from backend.models import PipelineError
from backend.tools.actions_runner import ActionsRunner
from backend.tools.files import read_files
from backend.repository_configuration import SetupConfig


class RepositoryRunner(ActionsRunner):
    def __init__(self, recipe, **kwargs):
        super().__init__(recipe, **kwargs)
        self.ref = os.getenv('TORQUE_REPOSITORY_ACTIONS_REF', 'torque-repository-runner-v4')
        self.profile = 'repository-tests'
        settings = dict(recipe.repository_setup or {})
        self.suite_sha = settings.pop('suite_sha', '')
        self.config = SetupConfig.model_validate(settings)
        if not re.fullmatch('[a-f0-9]{40}', self.suite_sha):
            raise PipelineError('Invalid frozen test revision')

    def preflight(self):
        super().preflight()
        workflow = self._request('GET', f'/repos/{self.repository}/contents/.github/workflows/{self.workflow}',
                                 params={'ref': self.workflow_sha}).json()
        if workflow.get('encoding') != 'base64' or workflow.get('size', 0) > 20000:
            raise PipelineError('Repository onboarding workflow unavailable')
        if 'TORQUE_REPOSITORY_SETUP' not in base64.b64decode(workflow['content']).decode():
            raise PipelineError('Ship the repository onboarding workflow before enabling repositories')

    def bind_source(self, owner, repo, sha):
        if not re.fullmatch('[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', f'{owner}/{repo}') or not re.fullmatch('[a-f0-9]{40}', sha):
            raise PipelineError('Invalid repository source')
        self.source_repository, self.source = f'{owner}/{repo}'.lower(), sha

    def dispatch(self, request_id, replacements):
        raw = json.dumps(replacements).encode()
        bundle = base64.b64encode(zlib.compress(raw)).decode()
        if len(raw) > 250000 or len(bundle) > 60000:
            raise PipelineError('Repository changes exceed workflow input limits')
        self._request('POST', f'/repos/{self.repository}/actions/workflows/{self.workflow}/dispatches',
                      json={'ref': self.ref, 'inputs': {'request_id': request_id,
                            'source_sha': self.source, 'source_repository': self.source_repository,
                            'acceptance_profile': self.profile, 'files_bundle': bundle,
                            'repository_setup': json.dumps({**self.config.model_dump(), 'editable_files': self.recipe.editable_files, 'suite_sha': self.suite_sha})}})

    def run(self, workspace, checkpoint):
        self.preflight()
        if self.source is None:
            raise PipelineError('Repository source has not been pinned')
        files = read_files(Path(workspace), self.recipe.editable_files)
        request_id = uuid.uuid4().hex
        checkpoint()
        self.dispatch(request_id, {name: item['content'] for name, item in files.items()})
        deadline = self.clock() + 600
        run = None
        try:
            while self.clock() < deadline:
                checkpoint()
                if run is None:
                    runs = self._request('GET', f'/repos/{self.repository}/actions/workflows/{self.workflow}/runs',
                                         params={'event': 'workflow_dispatch', 'per_page': 100}).json()['workflow_runs']
                    run = next((r for r in runs if r['display_title'] == 'Torque test ' + request_id), None)
                else:
                    run = self._request('GET', f'/repos/{self.repository}/actions/runs/{run["id"]}').json()
                if run:
                    if run['head_sha'] != self.workflow_sha:
                        raise PipelineError('Repository test workflow revision changed')
                    if run['status'] == 'completed':
                        return self._completed_result(run, request_id, checkpoint)
                self.pause(3)
            raise PipelineError('Repository tests timed out')
        finally:
            if run and run['status'] != 'completed':
                try: self._request('POST', f'/repos/{self.repository}/actions/runs/{run["id"]}/cancel')
                except PipelineError: pass
