import os
from typing import Literal

from langchain_mcp_adapters.client import MultiServerMCPClient


def get_tool_tags(tool) -> list[str]:
    return (tool.metadata or {}).get("_meta", {}).get("fastmcp", {}).get("tags", [])


async def load_researcher_tools(
    search_platform: Literal["tavily", "exa", "duckduckgo"] = "exa",
):
    client = MultiServerMCPClient(
        {
            "myMcpServer": {
                "transport": "http",
                "url": os.getenv("MCP_SERVER_URL"),
            }
        }
    )

    tools = await client.get_tools()

    researcher_tools = [
        tool for tool in tools if search_platform in get_tool_tags(tool)
    ]

    return researcher_tools
