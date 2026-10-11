"""Read-only GitHub issue access. Publication remains a separate milestone."""
import httpx
from backend.models import parse_issue

class GitHub:
    def __init__(self, token="", transport=None):
        headers = {"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2026-03-10"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.Client(base_url="https://api.github.com",headers=headers,
                                   timeout=20,follow_redirects=False,transport=transport)

    def issue(self, url):
        owner, repository, number = parse_issue(url)
        response = self.client.get(f"/repos/{owner}/{repository}/issues/{number}")
        response.raise_for_status()
        issue = response.json()
        if "pull_request" in issue:
            raise ValueError("URL identifies a pull request, not an issue")
        return {"title":issue["title"][:500],"state":issue["state"],"url":url,
                "body":(issue.get("body") or "")[:20000]}

    def revision(self, owner, repository):
        from urllib.parse import quote
        response = self.client.get(f"/repos/{owner}/{repository}")
        response.raise_for_status()
        branch = response.json()["default_branch"]
        response = self.client.get(f"/repos/{owner}/{repository}/commits/{quote(branch,safe='')}")
        response.raise_for_status()
        sha = response.json()["sha"]
        import re
        if not re.fullmatch("[0-9a-f]{40}",sha):
            raise ValueError("Invalid GitHub revision")
        return sha

    def close(self):
        self.client.close()
