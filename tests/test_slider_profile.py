import base64
import json
import zlib
import httpx
import pytest
from backend.acceptance_profiles import SLIDER_SHA,SLIDER_FILES,SLIDER_CRITERIA,validate_source
from backend.execution import Recipe
from backend.models import PipelineError,TestResult as RemoteResult
from backend.remote_job import decode_gallery_bundle

def decode_slider_bundle(value): return decode_gallery_bundle(value,SLIDER_FILES)
from backend.tools.actions_runner import ActionsRunner


def policy():
    return Recipe(image='remote-managed',command=['python','/acceptance/test_slider.py'],
                  context_files=SLIDER_FILES,editable_files=SLIDER_FILES,
                  acceptance_criteria=SLIDER_CRITERIA,suite_directory='remote-managed')


def bundle(value):return base64.b64encode(zlib.compress(json.dumps(value).encode())).decode()


@pytest.mark.parametrize('value',[
    {'../../.env':'secret'},
    {SLIDER_FILES[0]:'source'},
    {SLIDER_FILES[0]:42,SLIDER_FILES[1]:'css'},
    {SLIDER_FILES[0]:'source',SLIDER_FILES[1]:'css','package.json':'script'},
    {SLIDER_FILES[0]:'x'*250001,SLIDER_FILES[1]:'css'},
])
def test_slider_bundle_rejects_scope_types_and_compression_bombs(value):
    with pytest.raises(ValueError):decode_slider_bundle(bundle(value))


def test_slider_requires_reviewed_fork_revision_and_exact_criteria():
    assert validate_source('slider-keyboard','davre001/kokon',SLIDER_SHA)
    assert not validate_source('slider-keyboard','gabrielelozupone/kokon',SLIDER_SHA)
    runner=ActionsRunner(policy(),client=httpx.Client())
    try:
        with pytest.raises(PipelineError):runner.bind_source('davre001','kokon','a'*40)
        runner.bind_source('davre001','kokon',SLIDER_SHA)
        runner.recipe.acceptance_criteria=['weakened']*5
        with pytest.raises(PipelineError,match='scope'):runner.bind_source('davre001','kokon',SLIDER_SHA)
    finally:runner.close()


def test_slider_dispatch_contains_only_reviewed_files_and_source(tmp_path,monkeypatch):
    monkeypatch.setenv('TORQUE_ACTIONS_TOKEN','fixture-token')
    contents={SLIDER_FILES[0]:'public TSX',SLIDER_FILES[1]:'public CSS'}
    for name,content in contents.items():
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
    request_id=[None]
    def respond(request):
        if request.method=='POST':
            body=json.loads(request.content);inputs=body['inputs'];request_id[0]=inputs['request_id']
            assert inputs['acceptance_profile']=='slider-keyboard'
            assert inputs['source_repository']=='davre001/kokon'
            assert inputs['source_sha']==SLIDER_SHA and inputs['index_html']==''
            assert decode_slider_bundle(inputs['files_bundle'])==contents
            assert 'fixture-token' not in request.content.decode()
            return httpx.Response(204)
        if '/commits/' in request.url.path:return httpx.Response(200,json={'sha':'b'*40})
        if '/contents/' in request.url.path:
            content=base64.b64encode(b'files_bundle: acceptance_profile: slider-keyboard TORQUE_FILES_BUNDLE TORQUE_ACCEPTANCE_PROFILE').decode()
            return httpx.Response(200,json={'encoding':'base64','size':100,'content':content})
        if request.url.path.endswith('/runs'):
            return httpx.Response(200,json={'workflow_runs':[{'id':17,'display_title':'Torque test '+request_id[0],'status':'completed','head_sha':'b'*40}]})
        return httpx.Response(200,json={'state':'active'})
    client=httpx.Client(base_url='https://api.github.com',transport=httpx.MockTransport(respond))
    runner=ActionsRunner(policy(),client=client,pause=lambda _:None)
    runner.bind_source('davre001','kokon',SLIDER_SHA)
    runner._result=lambda run,rid:RemoteResult(exit_code=0,output='fixture',command=['remote'],assertions_passed=5)
    try:assert runner.run(tmp_path,lambda:None).passed
    finally:runner.close()


def test_slider_blocks_old_workflow_before_dispatch(monkeypatch):
    monkeypatch.setenv('TORQUE_ACTIONS_TOKEN','fixture-token')
    def respond(request):
        assert request.method=='GET'
        if '/contents/' in request.url.path:
            return httpx.Response(200,json={'encoding':'base64','size':10,'content':base64.b64encode(b'old workflow').decode()})
        return httpx.Response(200,json={'sha':'b'*40} if '/commits/' in request.url.path else {'state':'active'})
    runner=ActionsRunner(policy(),client=httpx.Client(base_url='https://api.github.com',transport=httpx.MockTransport(respond)))
    try:
        with pytest.raises(PipelineError,match='Push the gallery-capable workflow'):runner.preflight()
    finally:runner.close()
