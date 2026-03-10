import os

from dotenv import load_dotenv
import httpx
from mcp.client.streamable_http import streamable_http_client
from strands import Agent
from strands.tools.mcp import MCPClient, ToolFilters

load_dotenv()

PROJECT_ID = os.environ["NEON_PROJECT_ID"]
DATABASE = os.environ["NEON_DATABASE"]
BRANCH = os.environ["NEON_BRANCH"]
API_KEY = os.environ["NEON_API_KEY"]
NEON_MCP_URL = os.environ.get("NEON_MCP_URL", "https://mcp.neon.tech/mcp")


def create_neon_mcp_client(
    tool_filters: ToolFilters | None = None,
    *,
    read_only: bool = False,
) -> MCPClient:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }

    if read_only:
        headers["X-READ-ONLY"] = "true"

    return MCPClient(
        lambda: streamable_http_client(
            NEON_MCP_URL,
            http_client=httpx.AsyncClient(headers=headers),
        ),
        tool_filters=tool_filters,
    )


def run_neon_agent(
    *,
    system_prompt: str,
    query: str,
    tool_filters: ToolFilters | None = None,
    read_only: bool = False,
) -> str:
    mcp_client = create_neon_mcp_client(
        tool_filters=tool_filters,
        read_only=read_only,
    )

    with mcp_client:
        agent = Agent(
            system_prompt=system_prompt,
            tools=mcp_client.list_tools_sync(),
        )
        return str(agent(query))