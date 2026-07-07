import json
import os

from langchain_tavily import TavilySearch
from langchain_exa import ExaSearchResults
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchResults

from fastmcp import FastMCP

load_dotenv()

search_mcp = FastMCP("search")


@search_mcp.tool(tags={"tavily"})
def tavily_search(query: str) -> str:
    """
    Search the web using Tavily and return the results.
    """
    search_tool = TavilySearch(
        max_results=5,
        topic="general",
    )

    result = search_tool._run(query)

    return json.dumps(result.model_dump())


@search_mcp.tool(tags={"exa"})
def exa_search_tool(query: str) -> str:
    """
    Search the web using Exa and return the results.
    """
    EXA_API_KEY = os.environ.get("EXA_API_KEY")

    search_tool = ExaSearchResults(exa_api_key=EXA_API_KEY)

    result = search_tool._run(query, num_results=5)

    results = [
        {
            "title": r.title,
            "url": r.url,
            "text": r.text,
        }
        for r in result.results
    ]

    return json.dumps(results)


@search_mcp.tool(tags={"duckduckgo"})
def duckduckgo_search_tool(query: str) -> str:
    """
    Search the web using DuckDuckGo and return the results.
    """

    search_tool = DuckDuckGoSearchResults(num_results=5, handle_tool_error=True)

    result = search_tool._run(query)

    return json.dumps(result.model_dump())
