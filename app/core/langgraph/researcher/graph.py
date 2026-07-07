from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.langgraph.researcher.nodes import executor
from app.core.langgraph.tools.mcp import load_researcher_tools
from app.schemas.graph import ResearchAgentState


async def get_graph():
    researcher_builder = StateGraph(ResearchAgentState)

    tools_list = await load_researcher_tools(search_platform="exa")

    researcher_builder.add_node("executor", executor)
    researcher_builder.add_node("tools", ToolNode(tools_list))

    researcher_builder.set_entry_point("executor")
    researcher_builder.add_conditional_edges(
        "executor", tools_condition, ["tools", END]
    )
    researcher_builder.add_edge("tools", "executor")

    researcher_agent = researcher_builder.compile()

    return researcher_agent
