"""Neon MCP client factory for connecting sub-agents to the Neon database."""

import httpx
from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp import MCPClient

from server.config import get_settings


def get_neon_connection_details() -> tuple[str, str, str]:
    """Return (project_id, database, branch) for use in queries."""
    s = get_settings()
    return s.neon_project_id, s.neon_database, s.neon_branch_id


def create_neon_mcp_client() -> MCPClient:
    """Create a fresh Neon MCP client instance."""
    s = get_settings()
    return MCPClient(
        lambda: streamable_http_client(
            s.neon_mcp_url,
            http_client=httpx.AsyncClient(
                timeout=httpx.Timeout(120.0, connect=30.0),
                limits=httpx.Limits(max_keepalive_connections=0),
                headers={"Authorization": f"Bearer {s.neon_api_key}"}
            ),
        ),
    )