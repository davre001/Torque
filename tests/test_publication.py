import hashlib,json
from types import SimpleNamespace
import httpx
import pytest
from backend.publication import Publisher,verified_files
from backend.models import Conflict,Status
from backend.store import Store

SHA='a'*40
HEAD='c'*40
DEST='operator/demo'


def record():
    content='fixed\n'
    digest=hashlib.sha256(b'index.html\0'+content.encode()).hexdigest()
    return {'run_id':'1'*32,'created_at':1700000000,'issue_url':'https://github.com/source/demo/issues/4',
        'result':{'source_sha':SHA,'source_repository':'source/demo','verified':True,
        'plan':{'acceptance_criteria':['works']},'patch_sha256':digest,'verified_content_sha256':digest},
        'attempts':[{'number':1,'tests_passed':True,'patch_sha256':digest,
            'review':{'approved':True,'satisfied_criteria':[0]}}]}


def workspace(tmp_path):
    run=record()
    root=tmp_path/'workspaces'/run['run_id']
    root.mkdir(parents=True)
    (root/'index.html').write_bytes(b'fixed\n')
    artifacts=tmp_path/'artifacts'/run['run_id']
    artifacts.mkdir(parents=True)
    records={'patch-1.json':{'summary':'Fix','edits':[{'path':'index.html','original_sha256':'0'*64,'content':'fixed\n'}]},
        'tests-1.json':{'exit_code':0,'failure_kind':None,'timed_out':False,'assertions_passed':1}}
    run['result']['artifacts']=[]
    for name,value in records.items():
        data=json.dumps(value).encode()
        (artifacts/name).write_bytes(data)
        run['result']['artifacts'].append({'name':name,'sha256':hashlib.sha256(data).hexdigest()})
    recipe=SimpleNamespace(acceptance_criteria=['works'],context_files=['index.html'],editable_files=['index.html'])
    return run,recipe


def test_only_exact_verified_bytes_can_be_published(tmp_path):
    run,recipe=workspace(tmp_path)
    assert verified_files(run,recipe,tmp_path/'workspaces',tmp_path/'artifacts')=={'index.html':'fixed\n'}
    (tmp_path/'workspaces'/run['run_id']/'index.html').write_bytes(b'changed after testing')
    with pytest.raises(Conflict,match='Workspace changed'):
        verified_files(run,recipe,tmp_path/'workspaces',tmp_path/'artifacts')


def test_artifact_tampering_blocks_publication(tmp_path):
    run,recipe=workspace(tmp_path)
    (tmp_path/'artifacts'/run['run_id']/'tests-1.json').write_text('{}')
    with pytest.raises(Conflict,match='artifact changed'):
        verified_files(run,recipe,tmp_path/'workspaces',tmp_path/'artifacts')


def test_existing_windows_nested_patch_hash_can_be_published(tmp_path):
    run,recipe=workspace(tmp_path)
    root=tmp_path/'workspaces'/run['run_id']
    (root/'site').mkdir()
    (root/'index.html').rename(root/'site'/'index.html')
    recipe.context_files=recipe.editable_files=['site/index.html']
    run['result']['verified_content_sha256']=hashlib.sha256(b'site/index.html\0fixed\n').hexdigest()
    legacy=hashlib.sha256(b'site\\index.html\0fixed\n').hexdigest()
    run['result']['patch_sha256']=run['attempts'][0]['patch_sha256']=legacy
    artifact=tmp_path/'artifacts'/run['run_id']/'patch-1.json'
    patch=json.loads(artifact.read_bytes())
    patch['edits'][0]['path']='site/index.html'
    data=json.dumps(patch).encode()
    artifact.write_bytes(data)
    run['result']['artifacts'][0]['sha256']=hashlib.sha256(data).hexdigest()
    assert verified_files(run,recipe,tmp_path/'workspaces',tmp_path/'artifacts')=={'site/index.html':'fixed\n'}
    run['result']['patch_sha256']=run['attempts'][0]['patch_sha256']='f'*64
    with pytest.raises(Conflict,match='Patch does not match'):
        verified_files(run,recipe,tmp_path/'workspaces',tmp_path/'artifacts')


def test_publication_lock_and_real_pr_completion(tmp_path):
    clock=[1000]
    store=Store(tmp_path/'db',clock=lambda:clock[0]); store.initialize()
    run_id=store.submit('https://github.com/source/demo/issues/4')
    _,worker=store.claim(60)
    store.update(run_id,worker,Status.READY,result={'verified':True})
    owner=store.claim_publication(run_id,'operator',DEST)
    with pytest.raises(Conflict,match='already in progress'):
        store.claim_publication(run_id,'operator',DEST)
    with pytest.raises(Conflict,match='cannot be cancelled'):
        store.cancel(run_id,'operator')
    clock[0]+=901
    new_owner=store.claim_publication(run_id,'operator',DEST)
    with pytest.raises(Conflict,match='lease expired'):
        store.finish_publication(run_id,owner,pr_url='https://github.com/operator/demo/pull/1',commit_sha=HEAD)
    store.finish_publication(run_id,new_owner,error='retryable failure')
    assert store.get(run_id)['status']=='ready_to_publish'
    with pytest.raises(Conflict,match='destination cannot change'):
        store.claim_publication(run_id,'operator','operator/other')
    owner=store.claim_publication(run_id,'operator',DEST)
    store.finish_publication(run_id,owner,pr_url='https://github.com/operator/demo/pull/1',commit_sha=HEAD)
    assert store.get(run_id)['status']=='completed'
    assert store.history('operator')[0]['pr_url'].endswith('/pull/1')


def github_fixture(*,stale=False,wrong_owner=False,collision=False,timeout_on_pr=False,unrelated=False):
    state={'writes':[],'ref':None,'pr':None,'timed_out':False}
    content=b'fixed\n'
    blob=hashlib.sha1(f'blob {len(content)}\0'.encode()+content).hexdigest()
    def handler(request):
        path=request.url.path
        method=request.method
        data=json.loads(request.content) if request.content else {}
        if method!='GET':
            state['writes'].append((path,data))
        if path=='/user': value={'login':'operator'}
        elif path=='/repos/operator/demo':
            value={'id':2,'full_name':DEST,'owner':{'login':'other' if wrong_owner else 'operator'},
                   'permissions':{'push':True},'source':{'id':3 if unrelated else 1},'default_branch':'main'}
        elif path=='/repos/source/demo': value={'id':1}
        elif path.endswith('/commits/main'): value={'sha':'f'*40 if stale else SHA}
        elif path.endswith('/git/commits/'+SHA): value={'tree':{'sha':'b'*40}}
        elif '/git/trees/' in path:
            value={'truncated':False,'tree':[{'path':'index.html','type':'blob','mode':'100644',
                'sha':blob if path.endswith('e'*40) else 'd'*40}]}
        elif path.endswith('/git/trees'):
            assert data['base_tree']=='b'*40
            assert data['tree']==[{'path':'index.html','mode':'100644','type':'blob','content':'fixed\n'}]
            value={'sha':'e'*40}
        elif path.endswith('/git/commits'):
            assert data['parents']==[SHA] and data['author']==data['committer']
            value={'sha':HEAD,'tree':{'sha':'e'*40},'parents':[{'sha':SHA}]}
        elif '/git/ref/heads/torque/' in path:
            if collision: value={'object':{'sha':'f'*40}}
            elif state['ref']: value={'object':{'sha':state['ref']}}
            else: return httpx.Response(404,json={})
        elif path.endswith('/git/refs'):
            state['ref']=data['sha']; value={'object':{'sha':state['ref']}}
        elif path.endswith('/pulls') and method=='GET': value=[state['pr']] if state['pr'] else []
        elif path.endswith('/pulls'):
            assert data['base']=='main' and data['head']=='torque/'+'1'*32
            state['pr']={'head':{'sha':HEAD},'base':{'sha':SHA,'repo':{'full_name':DEST}},
                'body':data['body'],'state':'open','html_url':'https://github.com/operator/demo/pull/1'}
            if timeout_on_pr and not state['timed_out']:
                state['timed_out']=True
                raise httpx.ReadTimeout('private credentials must not escape')
            value=state['pr']
        else: raise AssertionError((method,path))
        return httpx.Response(200,json=value)
    return state,httpx.Client(base_url='https://api.github.com',transport=httpx.MockTransport(handler))


def test_pr_publication_is_idempotent_and_reconciles_ambiguous_timeout():
    from backend.models import PipelineError
    state,client=github_fixture(timeout_on_pr=True)
    publisher=Publisher('fixture-key',DEST,client)
    with pytest.raises(PipelineError,match='connection failed') as caught:
        publisher.publish(record(),{'index.html':'fixed\n'})
    assert 'private credentials' not in str(caught.value)
    assert publisher.publish(record(),{'index.html':'fixed\n'})==('https://github.com/operator/demo/pull/1',HEAD)
    assert len([p for p,_ in state['writes'] if p.endswith('/pulls')])==1
    assert not any('force' in data for _,data in state['writes'])


@pytest.mark.parametrize('option',['stale','wrong_owner','collision'])
def test_stale_base_owner_and_branch_collisions_are_rejected(option):
    state,client=github_fixture(**{option:True})
    with pytest.raises(Conflict):
        Publisher('fixture-key',DEST,client).publish(record(),{'index.html':'fixed\n'})
    assert not any(path.endswith('/pulls') for path,_ in state['writes'])
    if option!='collision':
        assert not state['writes']


def test_invalid_destination_does_not_lock_first_request(tmp_path,monkeypatch):
    import backend.publication as publication
    store=Store(tmp_path/'db');store.initialize()
    run_id=store.submit('https://github.com/source/demo/issues/4')
    _,worker=store.claim(60)
    store.update(run_id,worker,Status.READY,result=record()['result'])
    state,client=github_fixture(unrelated=True)
    monkeypatch.setenv('TORQUE_ALLOWED_REPOSITORIES','source/demo')
    monkeypatch.setattr(publication,'load_recipes',lambda:{'source/demo':object()})
    monkeypatch.setattr(publication,'verified_files',lambda *args:{'index.html':'fixed\n'})
    monkeypatch.setattr(publication,'Publisher',lambda token,destination:Publisher('fixture-key',destination,client))
    with pytest.raises(Conflict,match='not the verified source'):
        publication.publish_run(store,run_id,destination=DEST)
    assert not state['writes']
    with store.transaction() as db:
        assert db.execute('SELECT count(*) FROM publications WHERE run_id=?',(run_id,)).fetchone()[0]==0
    assert store.get(run_id)['status']=='ready_to_publish'
    assert store.claim_publication(run_id,'operator','operator/correct-fork')


@pytest.mark.parametrize('case',['single-rejection','unknown-usage','previous-retry','active-owner','wrong-user'])
def test_legacy_rejection_repair_preserves_ambiguous_and_active_locks(tmp_path,case):
    store=Store(tmp_path/'db');store.initialize()
    run_id=store.submit('https://github.com/source/demo/issues/4')
    _,worker=store.claim(60);store.update(run_id,worker,Status.READY,result={'verified':True})
    rejection='Destination is not the verified source repository or its fork'
    owner=store.claim_publication(run_id,'operator',DEST)
    if case=='previous-retry':
        store.finish_publication(run_id,owner,error='Remote usage unknown')
        owner=store.claim_publication(run_id,'operator',DEST)
    if case!='active-owner':
        store.finish_publication(run_id,owner,error='Remote usage unknown' if case=='unknown-usage' else rejection)
    released=store.release_rejected_publication(run_id,'other-user' if case=='wrong-user' else 'operator')
    assert released==(case=='single-rejection')
    if released:
        assert store.get(run_id)['error'] is None
        assert store.claim_publication(run_id,'operator','operator/correct-fork')
    else:
        with pytest.raises(Conflict,match='destination cannot change'):
            store.claim_publication(run_id,'operator','operator/correct-fork')
