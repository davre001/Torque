"""Live GitHub publication crash drill with isolated fixture state and no LLMs."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

import httpx
from backend.acceptance_profiles import GALLERY_FILES,GALLERY_CRITERIA
from backend.artifacts import Artifacts
from backend.config import ROOT,Settings
from backend.execution import Recipe
from backend.github_auth import GitHubAuth
from backend.lifecycle_probe import wait_for
from backend.models import Conflict,Status,TestResult
from backend.publication import Publisher,verified_files
from backend.store import Store

REPOSITORY='davre001/kokon'
USER='github:141245473'
PRODUCTION_RUN='b4064768c6b540a2852a172cbd6dbc1b'
REVIEWED_SHA='218143b523252ee95c2368adc83fef95b324b156'


def policy():
    return Recipe(image='remote-managed',command=['python','test_gallery.py'],
                  context_files=GALLERY_FILES,editable_files=GALLERY_FILES,
                  acceptance_criteria=GALLERY_CRITERIA,suite_directory='isolated-local-gallery-probe')


def token():
    production=Store(Settings.load().database)
    return GitHubAuth(production).authorize(USER,REPOSITORY,write=True)


def child(folder,phase):
    import backend.publication as publication
    folder=Path(folder)
    manifest=json.loads((folder/'manifest.json').read_text())
    store=Store(folder/'history.db',clock=lambda:time.time()+(901 if phase=='retry' else 0))
    os.environ['GITHUB_TOKEN']=token()
    os.environ['TORQUE_ALLOWED_REPOSITORIES']=REPOSITORY
    publication.ROOT=folder
    publication.load_recipes=lambda:{REPOSITORY:policy()}
    publication.workspace_root=lambda:folder/'var/workspaces'
    class ProbePublisher(Publisher):
        def request(self,method,path,**kwargs):
            if method=='POST' and path.endswith('/pulls'):
                kwargs['json']['title']='Torque lifecycle probe: publication crash recovery'
                kwargs['json']['body']=(
                    'Controlled publication lifecycle probe, not a new gallery bug fix.\n\n'
                    'Only a non-executing comment is added. The current gallery passes all four '
                    'local independent browser criteria with fixture I/O. Review is a deterministic '
                    'probe assertion, not an LLM review. No provider calls occurred.\n\n'
                    'The publisher is deliberately killed after PR creation and retried to verify '
                    'one-PR reconciliation. This PR stays draft and is not merged automatically.\n\n'
                    f'<!-- torque-run:{manifest["run_id"]} -->')
            response=super().request(method,path,**kwargs)
            with (folder/'requests.jsonl').open('a') as stream:
                stream.write(json.dumps({'phase':phase,'method':method,'path':path})+'\n')
            if phase=='crash' and method=='POST' and path.endswith('/pulls'):
                accepted={'pr_url':response['html_url'],'number':response['number'],
                          'head_sha':response['head']['sha'],'base_sha':response['base']['sha'],
                          'draft':response['draft']}
                (folder/'accepted.json').write_text(json.dumps(accepted))
                # Parent hard-kills this process before publish_run can save completion.
                while True:time.sleep(.1)
            return response
    publication.Publisher=ProbePublisher
    publication.publish_run(store,manifest['run_id'],destination=REPOSITORY)
    # Repeated completed publication must return without a new remote write.
    if phase=='retry':publication.publish_run(store,manifest['run_id'],destination=REPOSITORY)


def main():
    identifier=uuid.uuid4().hex
    folder=ROOT/'var/publication-crash-probe'/identifier;folder.mkdir(parents=True)
    store=Store(folder/'history.db');store.initialize()
    production=Store(Settings.load().database)
    original_run=production.get(PRODUCTION_RUN)
    assert original_run['status']=='completed'
    rid=store.submit('https://github.com/davre001/kokon/issues/4')
    workspace=folder/'var/workspaces'/rid
    auth_token=token()
    reader=Publisher(auth_token,REPOSITORY)
    processes=[]
    try:
        current=reader.request('GET','/repos/'+REPOSITORY+'/commits/master')['sha']
        assert current==REVIEWED_SHA,'Fork revision changed; review a fresh fixture before running'
        originals={}
        for name in GALLERY_FILES:
            response=httpx.get('https://raw.githubusercontent.com/'+REPOSITORY+'/'+current+'/'+name,timeout=30)
            response.raise_for_status();originals[name]=response.text
            target=workspace/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(response.text.encode())
        edited=GALLERY_FILES[0]
        content=originals[edited]+'\n// Torque publication lifecycle probe '+rid+': no runtime behavior change.\n'
        (workspace/edited).write_bytes(content.encode())
        environment={k:v for k,v in os.environ.items() if k.upper() in
                     {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','COMSPEC','PATHEXT'}}
        environment['NODE_PATH']=str(ROOT/'var/gallery-tools/node_modules')
        environment['TORQUE_TEST_BROWSER']=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
        test=subprocess.run([sys.executable,str(ROOT/'tests/acceptance/gallery/test_gallery.py'),str(workspace)],
                            env=environment,cwd=ROOT,capture_output=True,text=True,timeout=120)
        marker=next((line for line in test.stdout.splitlines() if line.startswith('TORQUE_TEST_RESULT=')),None)
        assert marker,'Browser suite did not produce a result'
        parsed=json.loads(marker.split('=',1)[1])
        assert test.returncode==0 and parsed=={'failure_kind':None,'assertions_passed':4},'Probe browser acceptance did not pass'
        artifacts=Artifacts(folder/'var/artifacts'/rid)
        records=[artifacts.write('patch-1',{'summary':'Controlled non-executing publication probe comment',
                    'edits':[{'path':edited,'original_sha256':hashlib.sha256(originals[edited].encode()).hexdigest(),'content':content}]}),
                 artifacts.write('tests-1',TestResult(exit_code=0,output=test.stdout,command=['local-gallery-browser'],assertions_passed=4).model_dump())]
        digest=hashlib.sha256()
        for name in sorted(GALLERY_FILES):digest.update(name.encode()+b'\0'+(workspace/name).read_bytes())
        patch_hash=hashlib.sha256(edited.encode()+b'\0'+content.encode()).hexdigest()
        result={'verified':True,'artifacts':records,'source_sha':current,'source_repository':REPOSITORY,
                'verified_content_sha256':digest.hexdigest(),'patch_sha256':patch_hash,
                'plan':{'summary':'Controlled publication crash fixture','acceptance_criteria':GALLERY_CRITERIA},
                'summary':'Controlled publication probe; only a non-executing comment is appended'}
        _,owner=store.claim(60)
        store.update(rid,owner,Status.READY,result=result,attempt={'number':1,'patch_sha256':patch_hash,'tests_passed':True,
                     'review':{'approved':True,'satisfied_criteria':[0,1,2,3],
                               'kind':'deterministic-probe-fixture','rationale':'Only the explicit appended comment differs; real browser acceptance passes.'}})
        verified_files(store.get(rid),policy(),folder/'var/workspaces',folder/'var/artifacts')
        (folder/'manifest.json').write_text(json.dumps({'run_id':rid}))
        def spawn(phase):
            p=subprocess.Popen([sys.executable,'-m','backend.publication_crash_probe','child',str(folder),phase],
                               cwd=ROOT,env=environment,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            processes.append(p);return p
        crash=spawn('crash')
        def accepted():
            if (folder/'accepted.json').exists():return json.loads((folder/'accepted.json').read_text())
            if crash.poll() is not None:raise RuntimeError('Publication child exited before PR acceptance; inspect isolated state')
            return False
        accepted_pr=wait_for(accepted,'PR acceptance barrier timed out',timeout=120)
        assert accepted_pr['draft'] and accepted_pr['base_sha']==current
        print('GitHub accepted '+accepted_pr['pr_url']+'; killing publisher before SQLite completion',flush=True)
        crash.kill();crash.wait(timeout=5)
        crashed=store.get(rid)
        assert crashed['status']=='publishing' and crashed['pr_url'] is None
        try:store.claim_publication(rid,'operator',REPOSITORY)
        except Conflict as exc:assert str(exc)=='Publication is already in progress'
        else:raise AssertionError('Active lease did not fence retry')
        retry=spawn('retry');retry.wait(timeout=120)
        assert retry.returncode==0,'Publication reconciliation failed; isolated state and draft PR retained'
        final=store.get(rid)
        assert final['status']=='completed' and final['pr_url']==accepted_pr['pr_url']
        assert final['result']['published_commit_sha']==accepted_pr['head_sha']
        prs=reader.request('GET','/repos/'+REPOSITORY+'/pulls',params={'state':'all','head':'davre001:torque/'+rid,'per_page':100})
        assert len(prs)==1 and prs[0]['head']['sha']==accepted_pr['head_sha'] and prs[0]['draft'] and prs[0]['state']=='open'
        requests=[json.loads(line) for line in (folder/'requests.jsonl').read_text().splitlines()]
        posts=[item for item in requests if item['method']=='POST' and item['path'].endswith('/pulls')]
        assert len(posts)==1
        unchanged=production.get(PRODUCTION_RUN)
        assert unchanged==original_run,'Original production run was unexpectedly modified'
        report={'mode':'live-github-publication-crash-isolated-fixture','probe_id':identifier,'run_id':rid,
                'source_repository':REPOSITORY,'source_sha':current,'pr_url':final['pr_url'],
                'published_commit_sha':accepted_pr['head_sha'],'crash_boundary':'After successful POST /pulls response, before SQLite completion',
                'status_after_kill':crashed['status'],'pr_url_after_kill':crashed['pr_url'],
                'active_lease_retry_rejected':True,'lease_expiry_mode':'Isolated Store clock advanced 901 seconds; no real 15-minute wait',
                'production_publication_lease_seconds':900,'status_after_retry':final['status'],
                'matching_pr_count':len(prs),'post_pulls_count':len(posts),'same_pr_and_head':True,
                'repeated_completed_request_no_new_pr':True,'draft':True,'merged':False,
                'browser_assertions_passed':4,'review_kind':'deterministic-probe-fixture, not an LLM review',
                'provider_calls':0,'production_run_modified':False,'fixture_database_isolated':True,
                'change':'Only a non-executing comment appended to Gallery.tsx; not a new issue fix',
                'requests':requests}
        evidence=ROOT/'evidence/publication-crash'/identifier;evidence.mkdir(parents=True)
        (evidence/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k!='requests'},indent=2),flush=True)
    finally:
        for process in processes:
            if process.poll() is None:process.kill();process.wait(timeout=5)
        reader.close()


if __name__=='__main__':
    if len(sys.argv)==1:main()
    elif len(sys.argv)==4 and sys.argv[1]=='child':
        try:child(sys.argv[2],sys.argv[3])
        except Exception as exc:
            (Path(sys.argv[2])/'child-error.json').write_text(json.dumps({'type':type(exc).__name__}))
            raise SystemExit(1)
    else:raise SystemExit('Unknown publication probe mode')
