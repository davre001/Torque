"""Interrupt one real gateway request in an isolated worker; never replay it."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from backend.config import ROOT, Settings
from backend.lifecycle_probe import settings, wait_for
from backend.models import Status
from backend.store import Store
from backend.worker import Worker


def child(database):
    from backend.execution import Limits
    from backend.integrations.litellm import LiteLLM
    from backend.integrations.providers import Budget
    from backend.runtime import rates
    Settings.load()
    folder=Path(database).parent
    store=Store(Path(database));store.initialize()
    def process(db,rid,owner,checkpoint):
        db.update(rid,owner,Status.INVESTIGATING)
        adapter=LiteLLM(os.environ['LITELLM_API_KEY'],os.environ['LITELLM_BASE_URL'],os.environ['LITELLM_MODEL'])
        prompt='Return a JSON object with a single boolean field named ok set to true.'
        budget=Budget(Limits(max_calls=1,max_tokens=3000,max_cost_usd=.02,max_output_tokens=128))
        reservation=budget.reserve(prompt,*rates('LITELLM'))
        # Persist conservative reservation before dispatch; do not claim billed usage.
        (folder/'reservation.json').write_text(json.dumps(budget.snapshot()))
        def started(request):
            (folder/'request-started').write_text('SDK HTTP request hook reached')
        adapter.client._client.event_hooks['request'].append(started)
        try:
            response=adapter.complete(prompt,128)
            (folder/'request-returned').write_text('provider response received')
            budget.settle(reservation,response,rates('LITELLM'))
            checkpoint()
        finally:
            adapter.close()
    Worker(store,settings(database),process).once()


def drill():
    identifier=uuid.uuid4().hex
    folder=ROOT/'var/lifecycle-probe'/identifier;folder.mkdir(parents=True)
    database=folder/'history.db';store=Store(database);store.initialize()
    rid=store.submit('https://github.com/fixture/lifecycle/issues/1')
    worker=None
    try:
        worker=subprocess.Popen([sys.executable,'-m','backend.provider_interruption_probe','child',str(database)],
                                cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        def started():
            if worker.poll() is not None:raise RuntimeError('Provider probe exited before dispatch; inspect configuration')
            return (folder/'request-started').exists()
        wait_for(started,'Provider probe did not start a request',timeout=20)
        time.sleep(.75)
        if worker.poll() is not None or (folder/'request-returned').exists():
            raise RuntimeError('Request finished before interruption; no interruption evidence recorded')
        worker.kill();worker.wait(timeout=5)
        time.sleep(3.2)
        # Reconcile through the real worker claim path without another model call.
        Worker(store,settings(database),lambda *args: (_ for _ in ()).throw(AssertionError('Unexpected replay'))).once()
        assert store.get(rid)['status']=='interrupted'
        with store.transaction() as db:
            executions=db.execute('SELECT executions FROM jobs WHERE run_id=?',(rid,)).fetchone()[0]
        assert executions==1
        report={'mode':'live-provider-process-interruption','probe_id':identifier,'run_id':rid,
                'status':'interrupted','executions':executions,'replayed':False,
                'request_hook_observed':True,'request_response_observed':False,
                'interruption':'hard process kill while synchronous gateway request was outstanding',
                'provider_acceptance':'unknown: no response; the request hook does not prove server acceptance',
                'billed_usage':'unknown; killing the client does not cancel server-side work',
                'reservation':json.loads((folder/'reservation.json').read_text()),
                'production_database_modified':False,'pr_writes':0}
        evidence=ROOT/'evidence/lifecycle'/identifier;evidence.mkdir(parents=True)
        (evidence/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    finally:
        if worker is not None and worker.poll() is None:worker.kill();worker.wait(timeout=5)


if __name__=='__main__':
    if len(sys.argv)==1:drill()
    elif len(sys.argv)==3 and sys.argv[1]=='child':child(sys.argv[2])
    else:raise SystemExit('Unknown provider interruption probe mode')
