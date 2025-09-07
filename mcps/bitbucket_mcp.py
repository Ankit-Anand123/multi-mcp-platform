#!/usr/bin/env python
"""
Bitbucket MCP Server (stdio) — ctx-free tools (compatible with Agno/Agent calls like list_repositories(ctx={}))

Run:
  uv run bitbucket_mcp.py

ENV (.env or process):
  BITBUCKET_URL=https://sourcecode.socialcoding.bosch.com/rest/api/1.0
  BITBUCKET_USERNAME=your-username
  BITBUCKET_PASSWORD=your-password-or-app-password
  BITBUCKET_PROJECT=ANALYTICS         # optional default project

  # For Bitbucket Cloud (optional):
  # BITBUCKET_URL=https://api.bitbucket.org/2.0
  # BITBUCKET_WORKSPACE=your-workspace

  # Optional:
  # BITBUCKET_VERIFY_SSL=true
  # HTTP(S)_PROXY, NO_PROXY are respected by requests
"""

from __future__ import annotations
import os
import sys
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------
# Logging (stderr only — stdout is reserved for MCP transport)
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stderr)
log = logging.getLogger("bitbucket-mcp")

# ---------------------------------------------------------------------
# Env & helpers
# ---------------------------------------------------------------------
load_dotenv()

def env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    return default if v is None else v.strip().lower() in {"1", "true", "yes", "y", "on"}

DEFAULT_TIMEOUT = (5, 30)  # connect, read

@dataclass
class Config:
    base_url: str
    username: str
    password: str
    verify_ssl: bool
    default_project: Optional[str]
    default_workspace: Optional[str]
    is_cloud: bool

def load_config() -> Config:
    base_url = (os.getenv("BITBUCKET_URL") or "").strip().rstrip("/")
    username = (os.getenv("BITBUCKET_USERNAME") or "").strip()
    password = (os.getenv("BITBUCKET_PASSWORD") or "").strip()
    verify_ssl = env_bool("BITBUCKET_VERIFY_SSL", True)
    default_project = os.getenv("BITBUCKET_PROJECT")
    default_workspace = os.getenv("BITBUCKET_WORKSPACE")
    is_cloud = "api.bitbucket.org/2.0" in base_url

    if not base_url:
        log.warning("BITBUCKET_URL is not set.")
    if not username or not password:
        log.warning("BITBUCKET_USERNAME or BITBUCKET_PASSWORD is not set.")

    return Config(
        base_url=base_url,
        username=username,
        password=password,
        verify_ssl=verify_ssl,
        default_project=default_project,
        default_workspace=default_workspace,
        is_cloud=is_cloud,
    )

# ---------------------------------------------------------------------
# Bitbucket client (works for Server/DC and Cloud)
# ---------------------------------------------------------------------
class BitbucketClient:
    def __init__(self, cfg: Config):
        if not cfg.base_url:
            raise ValueError("BITBUCKET_URL is not configured.")
        self.cfg = cfg
        s = requests.Session()
        if cfg.username and cfg.password:
            s.auth = HTTPBasicAuth(cfg.username, cfg.password)
        s.verify = cfg.verify_ssl
        self.sess = s

    def _check(self, r: requests.Response) -> Dict[str, Any]:
        if r.status_code >= 400:
            detail: Any
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            raise RuntimeError(f"Bitbucket API error {r.status_code}: {detail}")
        try:
            return r.json()
        except Exception as e:
            raise RuntimeError(f"Failed to parse JSON: {e}") from e

    # ---- Basic ping
    def ping(self) -> Dict[str, Any]:
        url = f"{self.cfg.base_url}/user" if self.cfg.is_cloud else f"{self.cfg.base_url}/application-properties"
        r = self.sess.get(url, timeout=DEFAULT_TIMEOUT)
        return {"ok": True, "data": self._check(r)}

    # ---- Projects
    def list_projects(self, limit: int = 100, start: int = 0) -> Dict[str, Any]:
        if self.cfg.is_cloud:
            # Cloud has no first-class "projects" list; synthesize from repos.
            repos = self.list_repositories(limit=limit, start=start)
            seen = {}
            for repo in repos.get("values", []):
                proj = repo.get("project") or {}
                key = proj.get("key") or proj.get("uuid") or "UNKNOWN"
                if key not in seen:
                    seen[key] = proj
            return {"values": list(seen.values())}
        url = f"{self.cfg.base_url}/projects"
        r = self.sess.get(url, params={"limit": limit, "start": start}, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    # ---- Repositories
    def list_repositories(self, project_key: Optional[str] = None, limit: int = 100, start: int = 0, search: Optional[str] = None) -> Dict[str, Any]:
        if self.cfg.is_cloud:
            if not self.cfg.default_workspace:
                raise ValueError("BITBUCKET_WORKSPACE is required for Cloud API.")
            url = f"{self.cfg.base_url}/repositories/{self.cfg.default_workspace}"
            params = {"pagelen": min(max(limit, 1), 100)}
            if search:
                params["q"] = f'name ~ "{search}"'
            r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            return self._check(r)
        pkey = project_key or self.cfg.default_project
        if not pkey:
            raise ValueError("project_key is required (or set BITBUCKET_PROJECT).")
        url = f"{self.cfg.base_url}/projects/{pkey}/repos"
        r = self.sess.get(url, params={"limit": limit, "start": start}, timeout=DEFAULT_TIMEOUT)
        data = self._check(r)
        if search:
            vals = data.get("values", [])
            vals = [v for v in vals if search.lower() in (v.get("name") or v.get("slug", "")).lower()]
            data = {**data, "values": vals}
        return data

    def get_repository(self, project_key: str, repo_slug: str) -> Dict[str, Any]:
        if self.cfg.is_cloud:
            if not self.cfg.default_workspace:
                raise ValueError("BITBUCKET_WORKSPACE is required for Cloud API.")
            url = f"{self.cfg.base_url}/repositories/{self.cfg.default_workspace}/{repo_slug}"
            r = self.sess.get(url, timeout=DEFAULT_TIMEOUT)
            return self._check(r)
        url = f"{self.cfg.base_url}/projects/{project_key}/repos/{repo_slug}"
        r = self.sess.get(url, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    # ---- Pull Requests
    def get_pull_requests(self, project_key: str, repo_slug: str, state: str = "OPEN", limit: int = 50, start: int = 0) -> Dict[str, Any]:
        if self.cfg.is_cloud:
            if not self.cfg.default_workspace:
                raise ValueError("BITBUCKET_WORKSPACE is required for Cloud API.")
            url = f"{self.cfg.base_url}/repositories/{self.cfg.default_workspace}/{repo_slug}/pullrequests"
            params = {"pagelen": min(max(limit, 1), 100)}
            if state:
                params["state"] = state.upper()
            r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            return self._check(r)
        url = f"{self.cfg.base_url}/projects/{project_key}/repos/{repo_slug}/pull-requests"
        params = {"limit": limit, "start": start}
        if state:
            params["state"] = state.upper()
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def create_pull_request(self, project_key: str, repo_slug: str, title: str, from_branch: str, to_branch: str, description: Optional[str] = None, reviewers: Optional[List[str]] = None) -> Dict[str, Any]:
        reviewers = reviewers or []
        if self.cfg.is_cloud:
            if not self.cfg.default_workspace:
                raise ValueError("BITBUCKET_WORKSPACE is required for Cloud API.")
            url = f"{self.cfg.base_url}/repositories/{self.cfg.default_workspace}/{repo_slug}/pullrequests"
            payload = {
                "title": title,
                "description": description or "",
                "source": {"branch": {"name": from_branch}},
                "destination": {"branch": {"name": to_branch}},
                "reviewers": [{"username": r} for r in reviewers],
            }
            r = self.sess.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
            return self._check(r)
        url = f"{self.cfg.base_url}/projects/{project_key}/repos/{repo_slug}/pull-requests"
        payload = {
            "title": title,
            "description": description or "",
            "fromRef": {"id": f"refs/heads/{from_branch}"},
            "toRef": {"id": f"refs/heads/{to_branch}"},
            "reviewers": [{"user": {"name": r}} for r in reviewers],
        }
        r = self.sess.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def approve_pull_request(self, project_key: str, repo_slug: str, pr_id: int) -> Dict[str, Any]:
        if self.cfg.is_cloud:
            if not self.cfg.default_workspace:
                raise ValueError("BITBUCKET_WORKSPACE is required for Cloud API.")
            url = f"{self.cfg.base_url}/repositories/{self.cfg.default_workspace}/{repo_slug}/pullrequests/{pr_id}/approve"
            r = self.sess.post(url, timeout=DEFAULT_TIMEOUT)
            return self._check(r)
        url = f"{self.cfg.base_url}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/approve"
        r = self.sess.post(url, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def unapprove_pull_request(self, project_key: str, repo_slug: str, pr_id: int) -> Dict[str, Any]:
        if self.cfg.is_cloud:
            if not self.cfg.default_workspace:
                raise ValueError("BITBUCKET_WORKSPACE is required for Cloud API.")
            url = f"{self.cfg.base_url}/repositories/{self.cfg.default_workspace}/{repo_slug}/pullrequests/{pr_id}/approve"
            r = self.sess.delete(url, timeout=DEFAULT_TIMEOUT)
            return {"ok": True} if r.status_code == 204 else self._check(r)
        url = f"{self.cfg.base_url}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/approve"
        r = self.sess.delete(url, timeout=DEFAULT_TIMEOUT)
        return {"ok": True} if r.status_code == 204 else self._check(r)

    def merge_pull_request(self, project_key: str, repo_slug: str, pr_id: int, version: Optional[int] = None) -> Dict[str, Any]:
        if self.cfg.is_cloud:
            url = f"{self.cfg.base_url}/repositories/{self.cfg.default_workspace}/{repo_slug}/pullrequests/{pr_id}/merge"
            r = self.sess.post(url, timeout=DEFAULT_TIMEOUT)
            return self._check(r)
        url = f"{self.cfg.base_url}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/merge"
        params = {}
        if version is not None:
            params["version"] = version
        r = self.sess.post(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)
        # ---- Pull Requests filtered to a destination branch (e.g., master)

    def get_pull_requests_to_branch(
        self,
        project_key: str,
        repo_slug: str,
        to_branch: str = "master",
        state: str = "ALL",
        limit: int = 50,
        start: int = 0,
    ) -> Dict[str, Any]:
        """
        Return PRs whose destination is the given branch (e.g., 'master').
        Cloud: server-side filter with 'q'.
        Server/DC: fetch + filter client-side on toRef.id/displayId.
        """
        if self.cfg.is_cloud:
            if not self.cfg.default_workspace:
                raise ValueError("BITBUCKET_WORKSPACE is required for Cloud API.")
            url = f"{self.cfg.base_url}/repositories/{self.cfg.default_workspace}/{repo_slug}/pullrequests"
            q = f'destination.branch.name = "{to_branch}"'
            params = {
                "pagelen": min(max(limit, 1), 100),
                "q": q,
            }
            if state and state.upper() != "ALL":
                params["state"] = state.upper()
            r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            return self._check(r)
        else:
            # Server/DC doesn't support branch filter in query; filter after fetch
            url = f"{self.cfg.base_url}/projects/{project_key}/repos/{repo_slug}/pull-requests"
            params = {"limit": limit, "start": start}
            if state:
                params["state"] = state.upper()
            r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            data = self._check(r)
            wanted = []
            for pr in data.get("values", []):
                toref = (pr or {}).get("toRef", {})
                # toRef.id is like "refs/heads/master"; displayId is "master"
                if toref.get("displayId") == to_branch or toref.get("id") == f"refs/heads/{to_branch}":
                    wanted.append(pr)
            data["values"] = wanted
            return data

    # ---- Commits within a PR
    def get_pull_request_commits(
        self,
        project_key: str,
        repo_slug: str,
        pr_id: int,
        limit: int = 100,
        start: int = 0,
    ) -> Dict[str, Any]:
        if self.cfg.is_cloud:
            if not self.cfg.default_workspace:
                raise ValueError("BITBUCKET_WORKSPACE is required for Cloud API.")
            url = f"{self.cfg.base_url}/repositories/{self.cfg.default_workspace}/{repo_slug}/pullrequests/{pr_id}/commits"
            params = {"pagelen": min(max(limit, 1), 100)}
            r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            return self._check(r)
        else:
            url = f"{self.cfg.base_url}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/commits"
            params = {"limit": limit, "start": start}
            r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            return self._check(r)

    # ---- Comments on a PR (with authors)
    # In BitbucketClient:

    def get_pull_request_comments(
        self,
        project_key: str,
        repo_slug: str,
        pr_id: int,
        limit: int = 100,
        start: int = 0,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return PR comments.
        - Cloud: native comments endpoint (no path required).
        - Server/DC:
            * If 'path' is provided -> use /comments?path=...
            * Else -> aggregate all comments from /activities (recommended).
        """
        if self.cfg.is_cloud:
            if not self.cfg.default_workspace:
                raise ValueError("BITBUCKET_WORKSPACE is required for Cloud API.")
            url = f"{self.cfg.base_url}/repositories/{self.cfg.default_workspace}/{repo_slug}/pullrequests/{pr_id}/comments"
            params = {"pagelen": min(max(limit, 1), 100)}
            r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            return self._check(r)

        # ---- Server/DC
        if path:
            # File-scoped comments — this is what the 400 was asking for
            url = f"{self.cfg.base_url}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments"
            params = {"limit": limit, "start": start, "path": path}
            r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            return self._check(r)

        # No path -> aggregate from activities to get ALL comments
        url = f"{self.cfg.base_url}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/activities"
        params = {"limit": limit, "start": start}
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        data = self._check(r)

        def _collect(ac):
            out = []
            # Common Server/DC activity structure: top-level 'comment' for new/root,
            # and nested replies in 'comment.comments'
            comment = ac.get("comment")
            if comment:
                out.extend(_flatten_comment(comment))
            # Some versions place comments under 'commentAction' etc.; try best-effort.
            ca = ac.get("commentAction")
            if isinstance(ca, dict) and ca.get("comment"):
                out.extend(_flatten_comment(ca["comment"]))
            return out

        def _flatten_comment(c):
            """Flatten a root comment + its replies into a simple list."""
            items = []
            items.append(_to_simple(c))
            for rep in (c.get("comments") or []):
                items.extend(_flatten_comment(rep))
            return items

        def _to_simple(c):
            author = (c.get("author") or {}).get("displayName") or (c.get("author") or {}).get("name")
            created = c.get("createdDate")  # ms epoch
            text = c.get("text") or c.get("content") or ""
            # Inline anchor info (file path / line)
            anchor = (c.get("anchor") or {})
            file_path = anchor.get("path")
            line = anchor.get("line")
            line_type = anchor.get("lineType")
            return {
                "id": c.get("id"),
                "author": author,
                "createdDate": created,
                "text": text,
                "filePath": file_path,
                "line": line,
                "lineType": line_type,
            }

        comments = []
        for ac in data.get("values", []):
            comments.extend(_collect(ac))

        # You can keep the activities paging info if you like:
        return {
            "values": comments,
            "size": len(comments),
            "isLastPage": data.get("isLastPage"),
            "nextPageStart": data.get("nextPageStart"),
        }


    # ---- Optional: PR diff (unified)
    def get_pull_request_diff(
        self,
        project_key: str,
        repo_slug: str,
        pr_id: int,
        context_lines: int = 3,
    ) -> Dict[str, Any]:
        """
        Return the textual diff as a string payload inside JSON: {"diff": "..."}.
        (Kept JSON-wrapped for MCP compatibility.)
        """
        if self.cfg.is_cloud:
            if not self.cfg.default_workspace:
                raise ValueError("BITBUCKET_WORKSPACE is required for Cloud API.")
            url = f"{self.cfg.base_url}/repositories/{self.cfg.default_workspace}/{repo_slug}/pullrequests/{pr_id}/diff"
            r = self.sess.get(url, timeout=DEFAULT_TIMEOUT)
            if r.status_code >= 400:
                return self._check(r)
            return {"diff": r.text}
        else:
            url = f"{self.cfg.base_url}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/diff"
            params = {"contextLines": max(0, int(context_lines))}
            r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            if r.status_code >= 400:
                return self._check(r)
            return {"diff": r.text}


# ---------------------------------------------------------------------
# Global, lazy-initialized client (no ctx needed)
# ---------------------------------------------------------------------
_CFG: Optional[Config] = None
_CLIENT: Optional[BitbucketClient] = None

def get_client() -> BitbucketClient:
    global _CFG, _CLIENT
    if _CFG is None:
        _CFG = load_config()
    if _CLIENT is None:
        _CLIENT = BitbucketClient(_CFG)
    return _CLIENT

def reload_env() -> Dict[str, Any]:
    """Reload .env and recreate the client (handy if you change creds without restarting)."""
    global _CFG, _CLIENT
    load_dotenv(override=True)
    _CFG = load_config()
    _CLIENT = BitbucketClient(_CFG)
    return {"ok": True}

# ---------------------------------------------------------------------
# MCP server & tools (NO ctx params)
# ---------------------------------------------------------------------
mcp = FastMCP("Bitbucket MCP (Python) — ctx-free")

@mcp.tool()
def ping() -> dict:
    """Health check against Bitbucket."""
    return get_client().ping()

@mcp.tool()
def reload_configuration() -> dict:
    """Reload .env and recreate the HTTP client."""
    return reload_env()

@mcp.tool()
def list_projects(limit: int = 100, start: int = 0) -> dict:
    """List projects (Server/DC). For Cloud, returns a synthesized list."""
    return get_client().list_projects(limit=limit, start=start)

@mcp.tool()
def list_repositories(project_key: Optional[str] = None, limit: int = 100, start: int = 0, search: Optional[str] = None) -> dict:
    """List repositories; accepts optional substring 'search' on name/slug."""
    return get_client().list_repositories(project_key=project_key, limit=limit, start=start, search=search)

@mcp.tool()
def get_repository(project_key: str, repo_slug: str) -> dict:
    """Get details of a repository."""
    return get_client().get_repository(project_key=project_key, repo_slug=repo_slug)

@mcp.tool()
def get_pull_requests(project_key: str, repo_slug: str, state: str = "OPEN", limit: int = 50, start: int = 0) -> dict:
    """List pull requests. state: OPEN|MERGED|DECLINED|ALL (Server/DC) or OPEN|MERGED|DECLINED (Cloud)."""
    return get_client().get_pull_requests(project_key=project_key, repo_slug=repo_slug, state=state, limit=limit, start=start)

@mcp.tool()
def create_pull_request(project_key: str, repo_slug: str, title: str, from_branch: str, to_branch: str, description: Optional[str] = None, reviewers: Optional[List[str]] = None) -> dict:
    """Create PR. reviewers: usernames (Cloud) or user.name (Server/DC)."""
    return get_client().create_pull_request(project_key, repo_slug, title, from_branch, to_branch, description, reviewers or [])

@mcp.tool()
def approve_pull_request(project_key: str, repo_slug: str, pr_id: int) -> dict:
    """Approve a PR."""
    return get_client().approve_pull_request(project_key, repo_slug, pr_id)

@mcp.tool()
def unapprove_pull_request(project_key: str, repo_slug: str, pr_id: int) -> dict:
    """Remove approval from a PR."""
    return get_client().unapprove_pull_request(project_key, repo_slug, pr_id)

@mcp.tool()
def merge_pull_request(project_key: str, repo_slug: str, pr_id: int, version: Optional[int] = None) -> dict:
    """Merge a PR. (Server/DC usually requires current PR version.)"""
    return get_client().merge_pull_request(project_key, repo_slug, pr_id, version)

@mcp.tool()
def get_commits(
    project_key: str,
    repo_slug: str,
    branch: Optional[str] = None,
    limit: int = 50,
    start: int = 0,
) -> dict:
    """List commits for a repo (and optional branch)."""
    client = get_client()
    if client.cfg.is_cloud:
        if not client.cfg.default_workspace:
            raise ValueError("BITBUCKET_WORKSPACE is required for Cloud API.")
        url = f"{client.cfg.base_url}/repositories/{client.cfg.default_workspace}/{repo_slug}/commits"
        if branch:
            url += f"/{branch}"
        params = {"pagelen": min(max(limit, 1), 100)}
        r = client.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return client._check(r)
    else:
        url = f"{client.cfg.base_url}/projects/{project_key}/repos/{repo_slug}/commits"
        params = {"limit": limit, "start": start}
        if branch:
            params["until"] = branch  # branch, tag, or commit id
        r = client.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return client._check(r)
    
@mcp.tool()
def get_pull_requests_to_branch(
    project_key: str,
    repo_slug: str,
    to_branch: str = "master",
    state: str = "ALL",
    limit: int = 50,
    start: int = 0,
) -> dict:
    """List PRs whose destination branch matches (e.g., master)."""
    return get_client().get_pull_requests_to_branch(project_key, repo_slug, to_branch, state, limit, start)

@mcp.tool()
def get_pull_request_commits(
    project_key: str,
    repo_slug: str,
    pr_id: int,
    limit: int = 100,
    start: int = 0,
) -> dict:
    """List commits inside a PR."""
    return get_client().get_pull_request_commits(project_key, repo_slug, pr_id, limit, start)

@mcp.tool()
def get_pull_request_comments(
    project_key: str,
    repo_slug: str,
    pr_id: int,
    limit: int = 100,
    start: int = 0,
    path: Optional[str] = None,
) -> dict:
    """List comments (with authors). If 'path' omitted on Server/DC, aggregates from activities to return ALL comments."""
    return get_client().get_pull_request_comments(project_key, repo_slug, pr_id, limit, start, path)


@mcp.tool()
def get_pull_request_diff(
    project_key: str,
    repo_slug: str,
    pr_id: int,
    context_lines: int = 3,
) -> dict:
    """Get unified diff text for a PR (wrapped as JSON: {'diff': '...'})"""
    return get_client().get_pull_request_diff(project_key, repo_slug, pr_id, context_lines)



def main() -> None:
    # stdio transport (works with Agno's MCPTools(command="..."))
    mcp.run()

if __name__ == "__main__":
    main()
