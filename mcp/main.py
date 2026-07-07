from dotenv import load_dotenv
from fastmcp import FastMCP

from tools.search import search_mcp

mcp = FastMCP("Deep researcher MCP")

load_dotenv()

mcp.mount(search_mcp)

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8081,
    )
