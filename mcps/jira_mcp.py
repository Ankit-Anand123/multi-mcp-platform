#!/usr/bin/env python
"""
JIRA MCP Server (stdio) — Operations for JIRA API

Run:
  uv run jira_mcp.py

ENV (.env or process):
  JIRA_URL=https://your-jira-instance.atlassian.net
  JIRA_USERNAME=your-email@company.com
  JIRA_TOKEN=your-api-token
  
  # Optional:
  # JIRA_VERIFY_SSL=true
"""

from __future__ import annotations
import os
import sys
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
import json

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stderr)
log = logging.getLogger("jira-mcp")

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
load_dotenv()

def env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    return default if v is None else v.strip().lower() in {"1", "true", "yes", "y", "on"}

DEFAULT_TIMEOUT = (5, 30)

@dataclass
class JiraConfig:
    base_url: str
    username: str
    token: str
    verify_ssl: bool

def load_jira_config() -> JiraConfig:
    base_url = (os.getenv("JIRA_URL") or "").strip().rstrip("/")
    username = (os.getenv("JIRA_USERNAME") or "").strip()
    token = (os.getenv("JIRA_TOKEN") or "").strip()
    verify_ssl = env_bool("JIRA_VERIFY_SSL", True)

    if not base_url:
        log.warning("JIRA_URL is not set.")
    if not username or not token:
        log.warning("JIRA_USERNAME or JIRA_TOKEN is not set.")

    return JiraConfig(
        base_url=base_url,
        username=username,
        token=token,
        verify_ssl=verify_ssl,
    )

# ---------------------------------------------------------------------
# JIRA client
# ---------------------------------------------------------------------
class JiraClient:
    def __init__(self, cfg: JiraConfig):
        if not cfg.base_url:
            raise ValueError("JIRA_URL is not configured.")
        if not cfg.username or not cfg.token:
            raise ValueError("JIRA_USERNAME or JIRA_TOKEN is not configured.")
        
        self.cfg = cfg
        self.api_base = f"{cfg.base_url}/rest/api/3"
        
        s = requests.Session()
        s.auth = HTTPBasicAuth(cfg.username, cfg.token)
        s.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        s.verify = cfg.verify_ssl
        self.sess = s

    def _check(self, r: requests.Response) -> Dict[str, Any]:
        if r.status_code >= 400:
            detail: Any
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            raise RuntimeError(f"JIRA API error {r.status_code}: {detail}")
        try:
            return r.json()
        except Exception as e:
            raise RuntimeError(f"Failed to parse JSON: {e}") from e

    # ---- Basic operations
    def ping(self) -> Dict[str, Any]:
        url = f"{self.api_base}/myself"
        r = self.sess.get(url, timeout=DEFAULT_TIMEOUT)
        return {"ok": True, "data": self._check(r)}

    # ---- Projects
    def get_projects(self, expand: Optional[str] = None) -> Dict[str, Any]:
        """Get all projects"""
        url = f"{self.api_base}/project"
        params = {}
        if expand:
            params["expand"] = expand
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def get_project(self, project_key: str, expand: Optional[str] = None) -> Dict[str, Any]:
        """Get project by key"""
        url = f"{self.api_base}/project/{project_key}"
        params = {}
        if expand:
            params["expand"] = expand
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    # ---- Issues
    def search_issues(self, jql: str, start_at: int = 0, max_results: int = 50, expand: Optional[str] = None, fields: Optional[str] = None) -> Dict[str, Any]:
        """Search issues using JQL"""
        url = f"{self.api_base}/search"
        payload = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
        }
        if expand:
            payload["expand"] = expand
        if fields:
            payload["fields"] = fields.split(",") if isinstance(fields, str) else fields
        
        r = self.sess.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def get_issue(self, issue_key: str, expand: Optional[str] = None, fields: Optional[str] = None) -> Dict[str, Any]:
        """Get issue by key"""
        url = f"{self.api_base}/issue/{issue_key}"
        params = {}
        if expand:
            params["expand"] = expand
        if fields:
            params["fields"] = fields
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def create_issue(self, project_key: str, summary: str, description: str, issue_type: str = "Task", **kwargs) -> Dict[str, Any]:
        """Create a new issue"""
        url = f"{self.api_base}/issue"
        
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description
                            }
                        ]
                    }
                ]
            },
            "issuetype": {"name": issue_type}
        }
        
        # Add additional fields
        fields.update(kwargs)
        
        payload = {"fields": fields}
        r = self.sess.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update issue fields"""
        url = f"{self.api_base}/issue/{issue_key}"
        payload = {"fields": fields}
        r = self.sess.put(url, json=payload, timeout=DEFAULT_TIMEOUT)
        return {"ok": True} if r.status_code == 204 else self._check(r)

    def assign_issue(self, issue_key: str, assignee: str) -> Dict[str, Any]:
        """Assign issue to user"""
        url = f"{self.api_base}/issue/{issue_key}/assignee"
        payload = {"accountId": assignee}
        r = self.sess.put(url, json=payload, timeout=DEFAULT_TIMEOUT)
        return {"ok": True} if r.status_code == 204 else self._check(r)

    def transition_issue(self, issue_key: str, transition_id: str, comment: Optional[str] = None) -> Dict[str, Any]:
        """Transition issue to new status"""
        url = f"{self.api_base}/issue/{issue_key}/transitions"
        payload = {
            "transition": {"id": transition_id}
        }
        if comment:
            payload["update"] = {
                "comment": [
                    {
                        "add": {
                            "body": {
                                "type": "doc",
                                "version": 1,
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": comment
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        
        r = self.sess.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        return {"ok": True} if r.status_code == 204 else self._check(r)

    def get_issue_transitions(self, issue_key: str) -> Dict[str, Any]:
        """Get available transitions for issue"""
        url = f"{self.api_base}/issue/{issue_key}/transitions"
        r = self.sess.get(url, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    # ---- Comments
    def get_issue_comments(self, issue_key: str, start_at: int = 0, max_results: int = 50) -> Dict[str, Any]:
        """Get comments for issue"""
        url = f"{self.api_base}/issue/{issue_key}/comment"
        params = {"startAt": start_at, "maxResults": max_results}
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def add_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
        """Add comment to issue"""
        url = f"{self.api_base}/issue/{issue_key}/comment"
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment
                            }
                        ]
                    }
                ]
            }
        }
        r = self.sess.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    # ---- Users
    def search_users(self, query: str, max_results: int = 50) -> Dict[str, Any]:
        """Search users"""
        url = f"{self.api_base}/user/search"
        params = {"query": query, "maxResults": max_results}
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def get_user(self, account_id: str) -> Dict[str, Any]:
        """Get user by account ID"""
        url = f"{self.api_base}/user"
        params = {"accountId": account_id}
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    # ---- Boards and Sprints (Agile)
    def get_boards(self, start_at: int = 0, max_results: int = 50) -> Dict[str, Any]:
        """Get agile boards"""
        url = f"{self.cfg.base_url}/rest/agile/1.0/board"
        params = {"startAt": start_at, "maxResults": max_results}
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def get_sprints(self, board_id: int, state: Optional[str] = None) -> Dict[str, Any]:
        """Get sprints for board"""
        url = f"{self.cfg.base_url}/rest/agile/1.0/board/{board_id}/sprint"
        params = {}
        if state:
            params["state"] = state
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def get_sprint_issues(self, sprint_id: int, start_at: int = 0, max_results: int = 50) -> Dict[str, Any]:
        """Get issues in sprint"""
        url = f"{self.cfg.base_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
        params = {"startAt": start_at, "maxResults": max_results}
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

# ---------------------------------------------------------------------
# Global client
# ---------------------------------------------------------------------
_CONFIG: Optional[JiraConfig] = None
_CLIENT: Optional[JiraClient] = None

def get_jira_client() -> JiraClient:
    global _CONFIG, _CLIENT
    if _CONFIG is None:
        _CONFIG = load_jira_config()
    if _CLIENT is None:
        _CLIENT = JiraClient(_CONFIG)
    return _CLIENT

def reload_jira_env() -> Dict[str, Any]:
    """Reload configuration"""
    global _CONFIG, _CLIENT
    load_dotenv(override=True)
    _CONFIG = None
    _CLIENT = None
    _CONFIG = load_jira_config()
    _CLIENT = JiraClient(_CONFIG)
    return {"ok": True, "config": {"base_url": _CONFIG.base_url, "has_token": bool(_CONFIG.token)}}

# ---------------------------------------------------------------------
# MCP server & tools
# ---------------------------------------------------------------------
mcp = FastMCP("JIRA MCP (Python)")

@mcp.tool()
def ping() -> dict:
    """Health check against JIRA."""
    return get_jira_client().ping()

@mcp.tool()
def reload_configuration() -> dict:
    """Reload .env and recreate the HTTP client."""
    return reload_jira_env()

# ---- Project operations
@mcp.tool()
def get_projects(expand: Optional[str] = None) -> dict:
    """Get all projects. expand: comma-separated list like 'description,lead'"""
    return get_jira_client().get_projects(expand=expand)

@mcp.tool()
def get_project(project_key: str, expand: Optional[str] = None) -> dict:
    """Get project by key. expand: comma-separated list like 'description,lead'"""
    return get_jira_client().get_project(project_key=project_key, expand=expand)

# ---- Issue operations
@mcp.tool()
def search_issues(jql: str, start_at: int = 0, max_results: int = 50, expand: Optional[str] = None, fields: Optional[str] = None) -> dict:
    """Search issues using JQL. Example: 'project = ABC AND status = Open'"""
    return get_jira_client().search_issues(jql=jql, start_at=start_at, max_results=max_results, expand=expand, fields=fields)

@mcp.tool()
def get_issue(issue_key: str, expand: Optional[str] = None, fields: Optional[str] = None) -> dict:
    """Get issue by key. expand: comma-separated list like 'changelog,renderedFields'"""
    return get_jira_client().get_issue(issue_key=issue_key, expand=expand, fields=fields)

@mcp.tool()
def create_issue(project_key: str, summary: str, description: str, issue_type: str = "Task") -> dict:
    """Create a new issue"""
    return get_jira_client().create_issue(project_key=project_key, summary=summary, description=description, issue_type=issue_type)

@mcp.tool()
def assign_issue(issue_key: str, assignee: str) -> dict:
    """Assign issue to user (use account ID)"""
    return get_jira_client().assign_issue(issue_key=issue_key, assignee=assignee)

@mcp.tool()
def get_issue_transitions(issue_key: str) -> dict:
    """Get available transitions for issue"""
    return get_jira_client().get_issue_transitions(issue_key=issue_key)

@mcp.tool()
def transition_issue(issue_key: str, transition_id: str, comment: Optional[str] = None) -> dict:
    """Transition issue to new status"""
    return get_jira_client().transition_issue(issue_key=issue_key, transition_id=transition_id, comment=comment)

# ---- Comment operations
@mcp.tool()
def get_issue_comments(issue_key: str, start_at: int = 0, max_results: int = 50) -> dict:
    """Get comments for issue"""
    return get_jira_client().get_issue_comments(issue_key=issue_key, start_at=start_at, max_results=max_results)

@mcp.tool()
def add_comment(issue_key: str, comment: str) -> dict:
    """Add comment to issue"""
    return get_jira_client().add_comment(issue_key=issue_key, comment=comment)

# ---- User operations
@mcp.tool()
def search_users(query: str, max_results: int = 50) -> dict:
    """Search users by name or email"""
    return get_jira_client().search_users(query=query, max_results=max_results)

@mcp.tool()
def get_user(account_id: str) -> dict:
    """Get user by account ID"""
    return get_jira_client().get_user(account_id=account_id)

# ---- Agile operations
@mcp.tool()
def get_boards(start_at: int = 0, max_results: int = 50) -> dict:
    """Get agile boards"""
    return get_jira_client().get_boards(start_at=start_at, max_results=max_results)

@mcp.tool()
def get_sprints(board_id: int, state: Optional[str] = None) -> dict:
    """Get sprints for board. state: active, closed, future"""
    return get_jira_client().get_sprints(board_id=board_id, state=state)

@mcp.tool()
def get_sprint_issues(sprint_id: int, start_at: int = 0, max_results: int = 50) -> dict:
    """Get issues in sprint"""
    return get_jira_client().get_sprint_issues(sprint_id=sprint_id, start_at=start_at, max_results=max_results)

def main() -> None:
    # stdio transport (works with Agno's MCPTools(command="..."))
    mcp.run()

if __name__ == "__main__":
    main()