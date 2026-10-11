"""Live subprocess lifecycle drill with fixture work and no provider/GitHub calls."""
import json
import os
from pathlib import Path
import socket
import signal
import subprocess
import sys
import time
import uuid
import httpx
from backend.config import ROOT, Settings
from backend.models import Cancelled, LeaseLost, Status
from backend.store import Store
from backend.worker import Worker


def settings(database):
    return Settings(Path(database), 'lifecycle-fixture-token', lease_seconds=3,
                    heartbeat_seconds=.5, poll_seconds=.1)


def child(database, stage):
    config=settings(database);store=Store(config.database);store.initialize()
    worker=None
    def process(db, rid, owner, checkpoint):
        db.update(rid,owner,Status(stage))
        while True:
            if (config.database.parent/'stop-requested').exists():
                worker.stop()
            checkpoint()
            time.sleep(.1)
    worker=Worker(store,config,process)
    signal.signal(signal.SIGINT,worker.stop)
    signal.signal(signal.SIGTERM,worker.stop)
    if hasattr(signal,'SIGBREAK'):
        signal.signal(signal.SIGBREAK,worker.stop)
    worker.once()


def api(database, port):
    # backend.api exports a default app at import; keep that import from loading
    # production .env values before constructing the isolated fixture app.
    import backend.config as config
    config.load_dotenv = lambda *args, **kwargs: None
    from backend.api import create_app
    import uvicorn
    uvicorn.run(create_app(settings(database)),host='127.0.0.1',port=int(port),access_log=False,log_level='error')


def wait_for(check, message, timeout=15):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        value=check()
        if value:return value
        time.sleep(.1)
    raise RuntimeError(message)


def drill():
    identifier=uuid.uuid4().hex
    folder=ROOT/'var'/'lifecycle-probe'/identifier;folder.mkdir(parents=True)
    database=folder/'history.db';store=Store(database);store.initialize()
    processes=[]
    # No root dotenv loading; no provider secrets inherited by subprocesses.
    environment={k:v for k,v in os.environ.items() if k.upper() in
                 {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','COMSPEC','PATHEXT'}}
    def spawn(mode, *args):
        options={}
        if os.name=='nt' and mode=='worker':
            startup=subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow=0
            options={'startupinfo':startup,'creationflags':subprocess.CREATE_NEW_CONSOLE|subprocess.CREATE_NEW_PROCESS_GROUP}
        p=subprocess.Popen([sys.executable,'-m','backend.lifecycle_probe',mode,str(database),*args],
                           cwd=ROOT,env=environment,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**options)
        processes.append(p);return p
    def submit():return store.submit('https://github.com/fixture/lifecycle/issues/1')
    outcomes=[]
    def record(case,rid,**details):
        run=store.get(rid)
        outcomes.append({'case':case,'run_id':rid,'status':run['status'],
                         'event_count':len(store.events(rid)),**details})
    def stage_ready(rid,stage):
        wait_for(lambda:store.get(rid)['status']==stage,'Worker did not enter fixture stage')
    headers={'Authorization':'Bearer lifecycle-fixture-token'}
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    def api_ready():
        try:return httpx.get(base+'/health',timeout=1).status_code==200
        except httpx.HTTPError:return False
    try:
        # Kill actual worker processes at each stage, then restart after lease expiry.
        for stage in ('investigating','implementing','verifying','recovering'):
            rid=submit();worker=spawn('worker',stage);stage_ready(rid,stage)
            with store.transaction() as db:
                owner=db.execute('SELECT owner FROM jobs WHERE run_id=?',(rid,)).fetchone()[0]
            worker.kill();worker.wait(timeout=5)
            time.sleep(3.2)
            restart=spawn('worker',stage);restart.wait(timeout=10)
            assert restart.returncode==0 and store.get(rid)['status']=='interrupted'
            with store.transaction() as db:
                assert db.execute('SELECT executions FROM jobs WHERE run_id=?',(rid,)).fetchone()[0]==1
            try:store.heartbeat(rid,owner,3)
            except LeaseLost:pass
            else:raise AssertionError('Stale worker owner accepted')
            record('hard-kill-restart-'+stage,rid,replayed=False,stale_owner_rejected=True)

        server=spawn('api',str(port));wait_for(api_ready,'Fixture API failed to start')
        rid=submit();response=httpx.post(base+'/api/runs/'+rid+'/cancel',headers=headers,timeout=5)
        assert response.status_code==200 and store.get(rid)['status']=='cancelled'
        worker=spawn('worker','investigating');worker.wait(timeout=10)
        with store.transaction() as db:
            assert db.execute('SELECT executions FROM jobs WHERE run_id=?',(rid,)).fetchone()[0]==0
        record('queued-api-cancellation',rid,executed=False)

        rid=submit();worker=spawn('worker','verifying');stage_ready(rid,'verifying')
        time.sleep(3.5)
        with store.transaction() as db:
            lease=db.execute('SELECT lease_until FROM jobs WHERE run_id=?',(rid,)).fetchone()[0]
        assert lease>time.time() and worker.poll() is None
        # Restart the API while the independent worker owns an active job.
        server.kill();server.wait(timeout=5);server=spawn('api',str(port));wait_for(api_ready,'API restart failed')
        response=httpx.get(base+'/api/runs/'+rid,headers=headers,timeout=5)
        assert response.status_code==200 and response.json()['status']=='verifying'
        record('api-restart-during-worker',rid,heartbeat_renewed=True)
        response=httpx.post(base+'/api/runs/'+rid+'/cancel',headers=headers,timeout=5)
        assert response.status_code==200
        worker.wait(timeout=10);assert worker.returncode==0 and store.get(rid)['status']=='cancelled'
        record('running-api-cancellation',rid,cooperative_exit=True)

        rid=submit();worker=spawn('worker','implementing');stage_ready(rid,'implementing')
        (folder/'stop-requested').write_text('fixture-trigger')
        worker.wait(timeout=10);assert worker.returncode==0 and store.get(rid)['status']=='interrupted'
        record('cooperative-worker-stop',rid,trigger='fixture calls Worker.stop; not an OS signal test')
        (folder/'stop-requested').unlink()
        if os.name != 'nt':
            for sig in (signal.SIGINT, signal.SIGTERM):
                rid=submit();worker=spawn('worker','implementing');stage_ready(rid,'implementing')
                worker.send_signal(sig);worker.wait(timeout=10)
                assert worker.returncode==0 and store.get(rid)['status']=='interrupted'
                record('os-signal-'+sig.name,rid,cooperative_exit=True)
        else:
            rid=submit();worker=spawn('worker','implementing');stage_ready(rid,'implementing')
            helper=subprocess.run([sys.executable,'-m','backend.lifecycle_probe','windows-break',str(worker.pid)],
                                  cwd=ROOT,env=environment,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
            assert helper.returncode==0
            worker.wait(timeout=10)
            assert worker.returncode==0 and store.get(rid)['status']=='interrupted'
            record('os-signal-SIGBREAK',rid,cooperative_exit=True,delivery='Windows GenerateConsoleCtrlEvent')
        report={'mode':'live-processes-fixture-work','run_id':identifier,'provider_calls':0,
                'github_calls':0,'remote_actions_cancellation_verified':False,
                'production_database_modified':False,'outcomes':outcomes}
        report['os_signal_check']='passed: Windows SIGBREAK; POSIX SIGINT/SIGTERM require Linux' if os.name=='nt' else 'passed: SIGINT and SIGTERM'
        evidence=ROOT/'evidence'/'lifecycle'/identifier;evidence.mkdir(parents=True)
        (evidence/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    finally:
        for p in processes:
            if p.poll() is None:p.kill();p.wait(timeout=5)


def remote_drill():
    from backend.execution import load_recipes
    from backend.tools.actions_runner import ActionsRunner
    Settings.load()
    runner=ActionsRunner(load_recipes()['gabrielelozupone/kokon'])
    request_id=None
    observed=None
    original=runner._request
    def request(method,path,**kwargs):
        nonlocal request_id
        result=original(method,path,**kwargs)
        if method=='POST' and path.endswith('/dispatches'):
            request_id=kwargs['json']['inputs']['request_id']
        return result
    runner._request=request
    def checkpoint():
        nonlocal observed
        if request_id:
            runs=original('GET',f'/repos/{runner.repository}/actions/workflows/{runner.workflow}/runs',
                          params={'event':'workflow_dispatch','per_page':20}).json()['workflow_runs']
            observed=next((r for r in runs if r['display_title']=='Torque test '+request_id),None)
            if observed and observed['status']=='in_progress':
                raise Cancelled('Explicit remote cancellation drill')
    try:
        runner.bind_source('GabrieleLozupone','kokon','995b078b79819c0049db3eef96fc6bd91b016b12')
        workspace=ROOT/'var/workspaces/b220ce7e5cda4e14963c74fc04ad8711'
        try:runner.run(workspace,checkpoint)
        except Cancelled:pass
        else:raise RuntimeError('Remote job completed before cancellation could be tested')
        assert observed is not None
        # The runner's finally block sends cancel for its correlated in-flight job.
        def cancelled():
            r=original('GET',f'/repos/{runner.repository}/actions/runs/{observed["id"]}').json()
            return r if r['status']=='completed' else False
        result=wait_for(cancelled,'Remote cancellation was not finalized',timeout=60)
        assert result['conclusion']=='cancelled'
        identifier=uuid.uuid4().hex
        report={'mode':'live-github-actions-cancellation','run_id':identifier,
                'request_id':request_id,'actions_run_id':result['id'],'actions_url':result['html_url'],
                'conclusion':result['conclusion'],'provider_calls':0,'pr_writes':0,
                'production_database_modified':False,'source':'cached reviewed public kokon workspace'}
        folder=ROOT/'evidence/lifecycle'/identifier;folder.mkdir(parents=True)
        (folder/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    finally:
        # Also reconcile a just-dispatched job if the checkpoint raised before the
        # runner's poll loop obtained its first run object.
        if observed:
            current=original('GET',f'/repos/{runner.repository}/actions/runs/{observed["id"]}').json()
            if current['status']!='completed':
                original('POST',f'/repos/{runner.repository}/actions/runs/{observed["id"]}/cancel')
        runner.close()


if __name__=='__main__':
    if len(sys.argv)==1:drill()
    elif sys.argv[1]=='--remote':remote_drill()
    elif sys.argv[1]=='worker':child(sys.argv[2],sys.argv[3])
    elif sys.argv[1]=='api':api(sys.argv[2],sys.argv[3])
    elif sys.argv[1]=='windows-break':
        import ctypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.FreeConsole()
        if not kernel.AttachConsole(int(sys.argv[2])):raise SystemExit(2)
        if not kernel.GenerateConsoleCtrlEvent(1,int(sys.argv[2])):raise SystemExit(3)
        time.sleep(.2)
        kernel.FreeConsole()
    else:raise SystemExit('Unknown lifecycle probe mode')
