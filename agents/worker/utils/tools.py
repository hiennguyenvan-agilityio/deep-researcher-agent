import os

from langchain_tavily import TavilySearch
from langchain_exa import ExaSearchResults
from dotenv import load_dotenv

load_dotenv()

tavily_search_tool = TavilySearch(
    max_results=5,
    topic="general",
)

exa_search_tool = ExaSearchResults(exa_api_key=os.environ["EXA_API_KEY"], max_results=5)
