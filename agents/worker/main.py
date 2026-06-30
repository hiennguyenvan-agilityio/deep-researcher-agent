from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agents.worker.utils.nodes import executor
from agents.worker.utils.states import SearchAgentState
from agents.worker.utils.tools import  exa_search_tool

worker_builder = StateGraph(SearchAgentState)

tools_list = [exa_search_tool]

worker_builder.add_node("executor", executor)
worker_builder.add_node("tools", ToolNode(tools_list))

worker_builder.set_entry_point("executor")
worker_builder.add_conditional_edges("executor", tools_condition, ["tools", END])
worker_builder.add_edge("tools", "executor")

worker_agent = worker_builder.compile()
