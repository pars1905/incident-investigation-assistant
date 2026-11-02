"""Read deployment metadata from GitHub's REST API."""
import json
import os
import re
import urllib.error
import urllib.request


SLUG = re.compile(r"^(?!\.+$)[A-Za-z0-9_.-]+$")


def get_deployments(owner, repo, service, opener=None):
    """Map GitHub deployments to the investigator's input schema.

    `service` is supplied by the operator; a deployment record alone does not
    prove which application service was released.
    """
    if not all(SLUG.fullmatch(value) for value in (owner, repo)):
        raise ValueError("Owner and repository must be simple GitHub names")
    if not service:
        raise ValueError("Service name required")
    url = f"https://api.github.com/repos/{owner}/{repo}/deployments?per_page=100"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "incident-portfolio-demo"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with (opener or urllib.request.urlopen)(request, timeout=10) as response:
            records = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"GitHub API returned HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach GitHub API: {error.reason}") from error
    if not isinstance(records, list):
        raise ValueError("Unexpected GitHub deployment response")
    return [{"id": str(record["id"]), "service": service, "at": record["created_at"],
             "source_url": f"https://github.com/{owner}/{repo}/deployments"} for record in records]


def get_workflow_runs(owner, repo, opener=None):
    """Read recent GitHub Actions runs as operational context, not root causes."""
    if not all(SLUG.fullmatch(value) for value in (owner, repo)):
        raise ValueError("Owner and repository must be simple GitHub names")
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=30"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "incident-portfolio-demo"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with (opener or urllib.request.urlopen)(request, timeout=10) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"GitHub API returned HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach GitHub API: {error.reason}") from error
    records = result.get("workflow_runs") if isinstance(result, dict) else None
    if not isinstance(records, list):
        raise ValueError("Unexpected GitHub workflow response")
    return [{"id": str(record["id"]), "name": record["name"],
             "status": record["status"], "conclusion": record.get("conclusion"),
             "at": record["created_at"], "source_url": record["html_url"]}
            for record in records]
