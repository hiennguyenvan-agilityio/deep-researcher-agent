from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.langgraph.worker.nodes import executor
from app.schemas.graph import SearchAgentState
from app.core.langgraph.tools.search import exa_search_tool

worker_builder = StateGraph(SearchAgentState)

tools_list = [exa_search_tool]

worker_builder.add_node("executor", executor)
worker_builder.add_node("tools", ToolNode(tools_list))

worker_builder.set_entry_point("executor")
worker_builder.add_conditional_edges("executor", tools_condition, ["tools", END])
worker_builder.add_edge("tools", "executor")

worker_agent = worker_builder.compile()
