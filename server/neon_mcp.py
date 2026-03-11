import os

from dotenv import load_dotenv
import httpx
from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp import MCPClient

load_dotenv()

PROJECT_ID = os.environ["NEON_PROJECT_ID"]
DATABASE = os.environ["NEON_DATABASE"]
BRANCH = os.environ["NEON_BRANCH"]

NEON_MCP_URL = os.environ.get("NEON_MCP_URL", "https://mcp.neon.tech/mcp")


def create_neon_mcp_client() -> MCPClient:
    api_key = os.environ["NEON_API_KEY"]
    return MCPClient(
        lambda: streamable_http_client(
            NEON_MCP_URL,
            http_client=httpx.AsyncClient(
                headers={"Authorization": f"Bearer {api_key}"}
            ),
        ),
    )