import asyncio
import os
from typing import Literal
from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient

from app.core.utils.https import make_pinned_httpx_client_factory

load_dotenv()

SearchPlatform = Literal["tavily", "exa", "duckduckgo"]

_tool_cache: dict[SearchPlatform, list] = {}
_tool_cache_lock = asyncio.Lock()

MCP_SEARCH_CERT_SHA256 = os.environ["MCP_SEARCH_CERT_SHA256"].lower()

# Unset/empty for a hosted server with a CA-signed cert: falls back to the
# system trust store instead of pinning a local self-signed file.
MCP_SEARCH_CERT_PATH = os.getenv("MCP_SEARCH_CERT_PATH") or None

client = MultiServerMCPClient(
    {
        "mySearchServer": {
            "transport": "http",
            "url": os.getenv("MCP_SERVER_URL"),
            "httpx_client_factory": make_pinned_httpx_client_factory(
                MCP_SEARCH_CERT_PATH, MCP_SEARCH_CERT_SHA256
            ),
        }
    }
)


def get_tool_tags(tool) -> list[str]:
    return (tool.metadata or {}).get("_meta", {}).get("fastmcp", {}).get("tags", [])


async def load_researcher_tools(
    search_platform: SearchPlatform = "exa",
    force: bool = False,
):
    if not force and (cached := _tool_cache.get(search_platform)):
        return cached

    async with _tool_cache_lock:
        # Re-check: a concurrent Send-dispatched searcher may have
        # populated the cache while we were waiting on the lock.
        if not force and (cached := _tool_cache.get(search_platform)):
            return cached

        filtered_tools = [
            tool
            for tool in await client.get_tools()
            if search_platform in get_tool_tags(tool)
        ]

        _tool_cache[search_platform] = filtered_tools

        return filtered_tools
