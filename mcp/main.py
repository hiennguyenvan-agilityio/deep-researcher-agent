from dotenv import load_dotenv
from fastmcp import FastMCP

from tools.search import search_mcp

mcp = FastMCP("Deep researcher MCP")

load_dotenv()

mcp.mount(search_mcp)

app = mcp.http_app()
