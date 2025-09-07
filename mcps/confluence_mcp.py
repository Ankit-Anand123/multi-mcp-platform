#!/usr/bin/env python
"""
Confluence MCP Server (stdio) — Read-only operations for Confluence API

Run:
  uv run confluence_mcp.py

ENV (.env or process):
  CONFLUENCE_URL=https://inside-docupedia.bosch.com/confluence/rest/api
  CONFLUENCE_TOKEN=your-bearer-token
  
  # Optional:
  # CONFLUENCE_VERIFY_SSL=true
  # HTTP(S)_PROXY, NO_PROXY are respected by requests
"""

from __future__ import annotations
import os
import sys
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
import urllib.parse

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------
# Logging (stderr only — stdout is reserved for MCP transport)
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stderr)
log = logging.getLogger("confluence-mcp")

# ---------------------------------------------------------------------
# Env & helpers
# ---------------------------------------------------------------------
load_dotenv()

def env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    return default if v is None else v.strip().lower() in {"1", "true", "yes", "y", "on"}

DEFAULT_TIMEOUT = (5, 30)  # connect, read

@dataclass
class ConfluenceConfig:
    base_url: str
    token: str
    verify_ssl: bool

def load_confluence_config() -> ConfluenceConfig:
    base_url = (os.getenv("CONFLUENCE_URL") or "").strip().rstrip("/")
    token = (os.getenv("CONFLUENCE_TOKEN") or "").strip()
    verify_ssl = env_bool("CONFLUENCE_VERIFY_SSL", True)

    if not base_url:
        log.warning("CONFLUENCE_URL is not set.")
    if not token:
        log.warning("CONFLUENCE_TOKEN is not set.")

    return ConfluenceConfig(
        base_url=base_url,
        token=token,
        verify_ssl=verify_ssl,
    )

# ---------------------------------------------------------------------
# Confluence client
# ---------------------------------------------------------------------
class ConfluenceClient:
    def __init__(self, cfg: ConfluenceConfig):
        if not cfg.base_url:
            raise ValueError("CONFLUENCE_URL is not configured.")
        if not cfg.token:
            raise ValueError("CONFLUENCE_TOKEN is not configured.")
        self.cfg = cfg
        s = requests.Session()
        # Set Authorization header with Bearer token
        s.headers.update({
            "Authorization": f"Bearer {cfg.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
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
            raise RuntimeError(f"Confluence API error {r.status_code}: {detail}")
        try:
            return r.json()
        except Exception as e:
            raise RuntimeError(f"Failed to parse JSON: {e}") from e

    # ---- Basic ping
    def ping(self) -> Dict[str, Any]:
        url = f"{self.cfg.base_url}/user/current"
        r = self.sess.get(url, timeout=DEFAULT_TIMEOUT)
        return {"ok": True, "data": self._check(r)}

    # ---- Space Operations
    def list_spaces(self, limit: int = 100, start: int = 0, expand: Optional[str] = None) -> Dict[str, Any]:
        """List all spaces"""
        url = f"{self.cfg.base_url}/space"
        params = {"limit": limit, "start": start}
        if expand:
            params["expand"] = expand
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def get_space(self, space_key: str, expand: Optional[str] = None) -> Dict[str, Any]:
        """Get space by key"""
        url = f"{self.cfg.base_url}/space/{space_key}"
        params = {}
        if expand:
            params["expand"] = expand
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def list_space_content(self, space_key: str, content_type: str = "page", limit: int = 100, start: int = 0, expand: Optional[str] = None) -> Dict[str, Any]:
        """List pages or blog posts in a space"""
        url = f"{self.cfg.base_url}/space/{space_key}/content/{content_type}"
        params = {"limit": limit, "start": start}
        if expand:
            params["expand"] = expand
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    # ---- Content Operations
    def get_content(self, content_id: str, expand: Optional[str] = None, version: Optional[int] = None) -> Dict[str, Any]:
        """Get content by ID"""
        url = f"{self.cfg.base_url}/content/{content_id}"
        params = {}
        if expand:
            params["expand"] = expand
        if version:
            params["version"] = version
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def search_content(self, cql: str, limit: int = 25, start: int = 0, expand: Optional[str] = None) -> Dict[str, Any]:
        """Search content using CQL"""
        url = f"{self.cfg.base_url}/content/search"
        params = {"cql": cql, "limit": limit, "start": start}
        if expand:
            params["expand"] = expand
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def get_content_children(self, content_id: str, child_type: str = "page", limit: int = 100, start: int = 0, expand: Optional[str] = None) -> Dict[str, Any]:
        """Get children of content (pages, comments, attachments)"""
        url = f"{self.cfg.base_url}/content/{content_id}/child/{child_type}"
        params = {"limit": limit, "start": start}
        if expand:
            params["expand"] = expand
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def get_content_history(self, content_id: str, limit: int = 25, start: int = 0, expand: Optional[str] = None) -> Dict[str, Any]:
        """Get content history"""
        url = f"{self.cfg.base_url}/content/{content_id}/history"
        params = {"limit": limit, "start": start}
        if expand:
            params["expand"] = expand
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def get_content_labels(self, content_id: str, limit: int = 100, start: int = 0) -> Dict[str, Any]:
        """Get content labels"""
        url = f"{self.cfg.base_url}/content/{content_id}/label"
        params = {"limit": limit, "start": start}
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    # ---- Comment Operations
    def get_comments(self, content_id: str, limit: int = 100, start: int = 0, expand: Optional[str] = None) -> Dict[str, Any]:
        """Get comments for content"""
        url = f"{self.cfg.base_url}/content/{content_id}/child/comment"
        params = {"limit": limit, "start": start}
        if expand:
            params["expand"] = expand
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    # ---- Attachment Operations
    def get_attachments(self, content_id: str, limit: int = 100, start: int = 0, expand: Optional[str] = None) -> Dict[str, Any]:
        """Get attachments for content"""
        url = f"{self.cfg.base_url}/content/{content_id}/child/attachment"
        params = {"limit": limit, "start": start}
        if expand:
            params["expand"] = expand
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    # ---- User Operations
    def get_current_user(self, expand: Optional[str] = None) -> Dict[str, Any]:
        """Get current user"""
        url = f"{self.cfg.base_url}/user/current"
        params = {}
        if expand:
            params["expand"] = expand
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def get_user(self, account_id: Optional[str] = None, username: Optional[str] = None, expand: Optional[str] = None) -> Dict[str, Any]:
        """Get user by accountId or username"""
        url = f"{self.cfg.base_url}/user"
        params = {}
        if account_id:
            params["accountId"] = account_id
        elif username:
            params["username"] = username
        else:
            raise ValueError("Either account_id or username must be provided")
        if expand:
            params["expand"] = expand
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def search_users(self, cql: str, limit: int = 25, start: int = 0, expand: Optional[str] = None) -> Dict[str, Any]:
        """Search users using CQL"""
        url = f"{self.cfg.base_url}/search/user"
        params = {"cql": cql, "limit": limit, "start": start}
        if expand:
            params["expand"] = expand
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    def get_user_content(self, account_id: str, limit: int = 25, start: int = 0, expand: Optional[str] = None) -> Dict[str, Any]:
        """Get user contributions"""
        url = f"{self.cfg.base_url}/user/{account_id}/content"
        params = {"limit": limit, "start": start}
        if expand:
            params["expand"] = expand
        r = self.sess.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._check(r)

    # ---- Helper methods for common search patterns
    def search_by_title(self, title: str, space_key: Optional[str] = None, content_type: str = "page") -> Dict[str, Any]:
        """Search content by title"""
        cql = f'title~"{title}" AND type={content_type}'
        if space_key:
            cql += f' AND space="{space_key}"'
        return self.search_content(cql)

    def search_by_text(self, text: str, space_key: Optional[str] = None, content_type: str = "page") -> Dict[str, Any]:
        """Search content by text"""
        cql = f'text~"{text}" AND type={content_type}'
        if space_key:
            cql += f' AND space="{space_key}"'
        return self.search_content(cql)

# ---------------------------------------------------------------------
# Global, lazy-initialized client
# ---------------------------------------------------------------------
_CONFIG: Optional[ConfluenceConfig] = None
_CLIENT: Optional[ConfluenceClient] = None

def get_confluence_client() -> ConfluenceClient:
    global _CONFIG, _CLIENT
    if _CONFIG is None:
        _CONFIG = load_confluence_config()
    if _CLIENT is None:
        _CLIENT = ConfluenceClient(_CONFIG)
    return _CLIENT

def reload_confluence_env() -> Dict[str, Any]:
    """Reload .env and recreate the client"""
    global _CONFIG, _CLIENT
    load_dotenv(override=True)
    _CONFIG = None  # Force recreation
    _CLIENT = None  # Force recreation
    _CONFIG = load_confluence_config()
    _CLIENT = ConfluenceClient(_CONFIG)
    return {"ok": True, "config": {"base_url": _CONFIG.base_url, "has_token": bool(_CONFIG.token)}}

# ---------------------------------------------------------------------
# MCP server & tools
# ---------------------------------------------------------------------
mcp = FastMCP("Confluence MCP (Python) — Read-only")

@mcp.tool()
def ping() -> dict:
    """Health check against Confluence."""
    return get_confluence_client().ping()

@mcp.tool()
def reload_configuration() -> dict:
    """Reload .env and recreate the HTTP client."""
    return reload_confluence_env()

# ---- Space Operations
@mcp.tool()
def list_spaces(limit: int = 100, start: int = 0, expand: Optional[str] = None) -> dict:
    """List all spaces. expand: comma-separated list like 'description,homepage'"""
    return get_confluence_client().list_spaces(limit=limit, start=start, expand=expand)

@mcp.tool()
def get_space(space_key: str, expand: Optional[str] = None) -> dict:
    """Get space by key. expand: comma-separated list like 'description,homepage'"""
    return get_confluence_client().get_space(space_key=space_key, expand=expand)

@mcp.tool()
def list_space_pages(space_key: str, limit: int = 100, start: int = 0, expand: Optional[str] = None) -> dict:
    """List pages in a space. expand: comma-separated list like 'body.view,version'"""
    return get_confluence_client().list_space_content(space_key=space_key, content_type="page", limit=limit, start=start, expand=expand)

@mcp.tool()
def list_space_blogs(space_key: str, limit: int = 100, start: int = 0, expand: Optional[str] = None) -> dict:
    """List blog posts in a space. expand: comma-separated list like 'body.view,version'"""
    return get_confluence_client().list_space_content(space_key=space_key, content_type="blogpost", limit=limit, start=start, expand=expand)

# ---- Content Operations
@mcp.tool()
def get_content(content_id: str, expand: Optional[str] = None, version: Optional[int] = None) -> dict:
    """Get content by ID. expand: comma-separated list like 'body.view,version,space'"""
    return get_confluence_client().get_content(content_id=content_id, expand=expand, version=version)

@mcp.tool()
def search_content(cql: str, limit: int = 25, start: int = 0, expand: Optional[str] = None) -> dict:
    """Search content using CQL. Example: 'text~"python" AND type=page AND space="ABC"'"""
    return get_confluence_client().search_content(cql=cql, limit=limit, start=start, expand=expand)

@mcp.tool()
def search_by_title(title: str, space_key: Optional[str] = None, content_type: str = "page") -> dict:
    """Search content by title. content_type: page, blogpost, comment, attachment"""
    return get_confluence_client().search_by_title(title=title, space_key=space_key, content_type=content_type)

@mcp.tool()
def search_by_text(text: str, space_key: Optional[str] = None, content_type: str = "page") -> dict:
    """Search content by text. content_type: page, blogpost, comment, attachment"""
    return get_confluence_client().search_by_text(text=text, space_key=space_key, content_type=content_type)

@mcp.tool()
def get_content_children(content_id: str, child_type: str = "page", limit: int = 100, start: int = 0, expand: Optional[str] = None) -> dict:
    """Get children of content. child_type: page, comment, attachment"""
    return get_confluence_client().get_content_children(content_id=content_id, child_type=child_type, limit=limit, start=start, expand=expand)

@mcp.tool()
def get_content_history(content_id: str, limit: int = 25, start: int = 0, expand: Optional[str] = None) -> dict:
    """Get content history. expand: comma-separated list like 'previousVersion,nextVersion'"""
    return get_confluence_client().get_content_history(content_id=content_id, limit=limit, start=start, expand=expand)

@mcp.tool()
def get_content_labels(content_id: str, limit: int = 100, start: int = 0) -> dict:
    """Get content labels"""
    return get_confluence_client().get_content_labels(content_id=content_id, limit=limit, start=start)

# ---- Comment and Attachment Operations
@mcp.tool()
def get_comments(content_id: str, limit: int = 100, start: int = 0, expand: Optional[str] = None) -> dict:
    """Get comments for content. expand: comma-separated list like 'body.view,version'"""
    return get_confluence_client().get_comments(content_id=content_id, limit=limit, start=start, expand=expand)

@mcp.tool()
def get_attachments(content_id: str, limit: int = 100, start: int = 0, expand: Optional[str] = None) -> dict:
    """Get attachments for content. expand: comma-separated list like 'version,container'"""
    return get_confluence_client().get_attachments(content_id=content_id, limit=limit, start=start, expand=expand)

# ---- User Operations
@mcp.tool()
def get_current_user(expand: Optional[str] = None) -> dict:
    """Get current user. expand: comma-separated list like 'operations,details'"""
    return get_confluence_client().get_current_user(expand=expand)

@mcp.tool()
def get_user(account_id: Optional[str] = None, username: Optional[str] = None, expand: Optional[str] = None) -> dict:
    """Get user by accountId or username. expand: comma-separated list like 'operations,details'"""
    return get_confluence_client().get_user(account_id=account_id, username=username, expand=expand)

@mcp.tool()
def search_users(cql: str, limit: int = 25, start: int = 0, expand: Optional[str] = None) -> dict:
    """Search users using CQL. Example: 'username~"john"'"""
    return get_confluence_client().search_users(cql=cql, limit=limit, start=start, expand=expand)

@mcp.tool()
def get_user_content(account_id: str, limit: int = 25, start: int = 0, expand: Optional[str] = None) -> dict:
    """Get user contributions. expand: comma-separated list like 'body.view,version'"""
    return get_confluence_client().get_user_content(account_id=account_id, limit=limit, start=start, expand=expand)

def main() -> None:
    # stdio transport (works with Agno's MCPTools(command="..."))
    mcp.run()

if __name__ == "__main__":
    main()