from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from planner_agent.utils.nodes import make_plan_node
from planner_agent.utils.states import PlannerAgentState
from tools.todo import write_todos


planner_builder = StateGraph(PlannerAgentState)

tools_list = [write_todos]

planner_builder.add_node("planning", make_plan_node)
planner_builder.add_node("tools", ToolNode(tools_list))

planner_builder.set_entry_point("planning")

planner_builder.add_edge("planning", "tools")
planner_builder.add_edge("tools", END)

planner_agent = planner_builder.compile()