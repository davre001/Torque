"""Run with python -m backend; CLI submissions use the same durable queue."""
import argparse
import json
import logging
import signal
from backend.config import Settings
from backend.models import SubmitRun, parse_issue
from backend.runtime import AgentProcessor, readiness
from backend.store import Store
from backend.worker import Worker

def main():
    parser = argparse.ArgumentParser(description="Torque local backend")
    commands = parser.add_subparsers(dest="command",required=True)
    worker_command = commands.add_parser('worker')
    worker_command.add_argument('--once',action='store_true')
    worker_command.add_argument('--run-id',help='Claim only this assigned run; implies --once')
    commands.add_parser('preflight').add_argument('--cloud-probe',action='store_true')
    commands.add_parser('migrate')
    commands.add_parser('dispatch')
    commands.add_parser("run").add_argument("issue_url")
    commands.add_parser("status").add_argument("run_id")
    commands.add_parser("publish").add_argument("run_id")
    retention = commands.add_parser('cleanup')
    retention.add_argument('--keep-days', type=float, default=7)
    retention.add_argument('--apply', action='store_true', help='Remove eligible runtime files; default only previews')
    args = parser.parse_args()
    if args.command == 'worker' and args.run_id:
        import re
        if not re.fullmatch('[a-f0-9]{32}', args.run_id):
            parser.error('Invalid assigned run ID')
    settings = Settings.load()
    import os
    target=os.getenv('TORQUE_MIGRATION_DATABASE_URL') if args.command=='migrate' else None
    store = Store(target or settings.database)
    store.initialize(migrate=args.command == 'migrate')
    if args.command == 'migrate':
        from backend.github_auth import GitHubAuth
        GitHubAuth(store).initialize()
        print(json.dumps({'schema_version':2,'storage':'postgresql' if store.database.postgres else 'sqlite'}))
    elif args.command == 'dispatch':
        from backend.dispatch import Dispatcher
        dispatcher = Dispatcher(store)
        try: print(json.dumps(dispatcher.reconcile()))
        finally: dispatcher.close()
    elif args.command == 'cleanup':
        from backend.retention import cleanup
        from backend.config import ROOT
        from backend.models import PipelineError
        try:
            print(json.dumps(cleanup(store, ROOT, args.keep_days, args.apply), indent=2))
        except PipelineError as exc:
            parser.error(str(exc))
    elif args.command == "preflight":
        from backend.cloud_preflight import check
        print(json.dumps({"storage":"ready","operator_access_configured":bool(settings.operator_token),
                          "allowed_repositories":list(settings.allowed_repositories),
                          "agent_pipeline":readiness(),'cloud':check(store,args.cloud_probe)}))
    elif args.command == "run":
        issue = SubmitRun(issue_url=args.issue_url)
        owner, repo, _ = parse_issue(issue.issue_url)
        if f"{owner}/{repo}".lower() not in settings.allowed_repositories:
            parser.error("Add repository to TORQUE_ALLOWED_REPOSITORIES first")
        from backend.admission import Admission
        from backend.models import AdmissionDenied
        try:
            run_id = store.submit(issue.issue_url,admission=Admission.load())
        except AdmissionDenied as exc:
            parser.error(str(exc))
        print(json.dumps({"run_id":run_id,"status":"queued"}))
    elif args.command == "status":
        record = store.get(args.run_id,"operator")
        if record is None:
            parser.error("Run not found")
        print(json.dumps(record,indent=2))
    elif args.command == "publish":
        from backend.publication import publish_run
        from backend.models import Conflict, PipelineError
        try:
            print(json.dumps(publish_run(store,args.run_id),indent=2))
        except (Conflict,PipelineError) as exc:
            parser.error(str(exc))
    else:
        logging.basicConfig(level=logging.INFO,format="%(asctime)s %(name)s: %(message)s")
        # Signed artifact URLs must not appear in HTTP client logs.
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        processor = AgentProcessor()
        worker = Worker(store,settings,processor)
        signal.signal(signal.SIGINT,worker.stop)
        signal.signal(signal.SIGTERM,worker.stop)
        if hasattr(signal,'SIGBREAK'):
            signal.signal(signal.SIGBREAK,worker.stop)
        try:
            if args.once or args.run_id:
                worker.once(args.run_id)
            else:
                worker.run()
        finally:
            processor.close()

if __name__ == "__main__":
    main()
