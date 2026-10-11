"""Run with python -m backend; CLI submissions use the same durable queue."""
import argparse
import json
import signal
from backend.config import Settings
from backend.models import SubmitRun, parse_issue
from backend.orchestrator import investigate
from backend.store import Store
from backend.worker import Worker

def main():
    parser = argparse.ArgumentParser(description="Torque local backend")
    commands = parser.add_subparsers(dest="command",required=True)
    commands.add_parser("worker").add_argument("--once",action="store_true")
    commands.add_parser("preflight")
    commands.add_parser("run").add_argument("issue_url")
    commands.add_parser("status").add_argument("run_id")
    args = parser.parse_args()
    settings = Settings.load()
    store = Store(settings.database)
    store.initialize()
    if args.command == "preflight":
        print(json.dumps({"storage":"ready","operator_access_configured":bool(settings.operator_token),
                          "allowed_repositories":list(settings.allowed_repositories),
                          "agent_pipeline_ready":False}))
    elif args.command == "run":
        issue = SubmitRun(issue_url=args.issue_url)
        owner, repo, _ = parse_issue(issue.issue_url)
        if f"{owner}/{repo}".lower() not in settings.allowed_repositories:
            parser.error("Add repository to TORQUE_ALLOWED_REPOSITORIES first")
        print(json.dumps({"run_id":store.submit(issue.issue_url),"status":"queued"}))
    elif args.command == "status":
        record = store.get(args.run_id,"operator")
        if record is None:
            parser.error("Run not found")
        print(json.dumps(record,indent=2))
    else:
        worker = Worker(store,settings,investigate)
        signal.signal(signal.SIGINT,worker.stop)
        signal.signal(signal.SIGTERM,worker.stop)
        if args.once:
            worker.once()
        else:
            worker.run()

if __name__ == "__main__":
    main()
