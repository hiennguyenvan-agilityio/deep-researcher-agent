import os
from typing import Literal
from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

SearchPlatform = Literal["tavily", "exa", "duckduckgo"]

_tool_cache: dict[SearchPlatform, list] = {}

client = MultiServerMCPClient(
    {
        "myMcpServer": {
            "transport": "http",
            "url": os.getenv("MCP_SERVER_URL"),
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

    filtered_tools = [
        tool
        for tool in await client.get_tools()
        if search_platform in get_tool_tags(tool)
    ]

    _tool_cache[search_platform] = filtered_tools

    return filtered_tools
