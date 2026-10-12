"""OS-signal shutdown during real HTTP I/O against a local provider fixture."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import httpx
from backend.config import ROOT
from backend.execution import Limits
from backend.integrations.providers import Budget, StructuredProvider
from backend.lifecycle_probe import settings, wait_for
from backend.models import Recovery, Status
from backend.store import Store
from backend.worker import Worker


def child(database, endpoint):
    store = Store(Path(database)); store.initialize()
    folder = Path(database).parent
    budget = Budget(Limits(max_calls=2, max_cost_usd=.1))
    class Adapter:
        model = 'local-blocked-http-fixture'
        def complete(self, *_):
            with httpx.Client(timeout=2, trust_env=False) as client:
                client.get(endpoint)
            raise AssertionError('Fixture must time out')
    def process(db, rid, owner, checkpoint):
        db.update(rid, owner, Status.INVESTIGATING)
        try:
            StructuredProvider(Adapter(), budget, 3, 15, checkpoint).ask('fixture', {}, Recovery)
        finally:
            (folder / 'budget.json').write_text(json.dumps(budget.snapshot()))
    worker = Worker(store, settings(database), process)
    for sig in (signal.SIGINT, signal.SIGTERM): signal.signal(sig, worker.stop)
    if hasattr(signal, 'SIGBREAK'): signal.signal(signal.SIGBREAK, worker.stop)
    worker.once()


def drill():
    identifier = uuid.uuid4().hex
    folder = ROOT / 'var/lifecycle-probe' / identifier; folder.mkdir(parents=True)
    database = folder / 'history.db'; store = Store(database); store.initialize()
    rid = store.submit('https://github.com/fixture/lifecycle/issues/1')
    started = threading.Event()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_): pass
        def do_GET(self):
            started.set(); time.sleep(3)  # No response before the client timeout.
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    environment = {k:v for k,v in os.environ.items() if k.upper() in
                   {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','COMSPEC','PATHEXT'}}
    options = {}
    if os.name == 'nt':
        startup = subprocess.STARTUPINFO(); startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        options = {'startupinfo':startup, 'creationflags':subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP}
    worker = subprocess.Popen([sys.executable, '-m', 'backend.blocked_shutdown_probe',
                               'child', str(database), f'http://127.0.0.1:{server.server_port}'],
                              cwd=ROOT, env=environment, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, **options)
    try:
        wait_for(started.is_set, 'Local blocked request did not start')
        before = time.monotonic()
        if os.name == 'nt':
            subprocess.run([sys.executable, '-m', 'backend.lifecycle_probe', 'windows-break', str(worker.pid)],
                           cwd=ROOT, env=environment, check=True, timeout=5, capture_output=True)
            delivered = 'Windows SIGBREAK'
        else:
            worker.send_signal(signal.SIGTERM); delivered = 'Linux SIGTERM'
        worker.wait(timeout=10)
        run = store.get(rid); budget = json.loads((folder/'budget.json').read_text())
        assert worker.returncode == 0 and run['status'] == 'interrupted'
        assert budget['calls'] == 1 and budget['usage'][0]['usage'] == 'request-failed-reserved'
        report = {'mode':'os-signal-during-local-blocked-http-provider-fixture', 'probe_id':identifier,
                  'run_id':rid, 'signal':delivered, 'status':run['status'], 'exit_code':worker.returncode,
                  'shutdown_seconds':round(time.monotonic()-before,3), 'budget':budget,
                  'transport_retried':False, 'real_provider_calls':0, 'production_database_modified':False,
                  'limitations':['Local HTTP fixture, not a real paid provider',
                                 'Shutdown waits for the adapter I/O timeout; remote work is not cancelled',
                                 'Production LiteLLM timeout is 45 seconds; Gemini is 120 seconds']}
        evidence = ROOT / 'evidence/lifecycle' / identifier; evidence.mkdir(parents=True)
        (evidence/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    finally:
        if worker.poll() is None: worker.kill(); worker.wait(timeout=5)
        server.shutdown(); server.server_close()


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'child': child(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 1: drill()
    else: raise SystemExit('Unknown blocked shutdown probe mode')
