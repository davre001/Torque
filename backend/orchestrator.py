"""Coordinator exports; investigate retains the read-only diagnostic milestone."""
import os
from backend.models import Status
from backend.integrations.github import GitHub
from backend.pipeline import Pipeline

def investigate(store, run_id, owner, checkpoint):
    checkpoint()
    record = store.get(run_id)
    store.update(run_id,owner,Status.INVESTIGATING)
    github = GitHub(os.getenv("GITHUB_TOKEN",""))
    try:
        issue = github.issue(record["issue_url"])
    finally:
        github.close()
    checkpoint()
    result = {"issue":issue,
              "milestone":"issue-context", "verified":False}
    store.update(run_id,owner,Status.FAILED,result=result,
                 error="Issue fetched. Agent editing, isolated tests, and publication are not implemented yet; no repository changes were made")
