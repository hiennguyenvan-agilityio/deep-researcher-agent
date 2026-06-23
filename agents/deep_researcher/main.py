import json

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.runnables import RunnableConfig
from langgraph.types import Send

from agents.deep_researcher.utils.nodes import finalize_node, gatekeeper_node, planning_node, research_node, synthesis_node, verification_node
from agents.deep_researcher.utils.states import AgentState
from resources.vitual_file_system import get_vfs
from tools.todo import completed_task, write_todos
from utils.common import get_next_todo
from functools import partial


def assign_task(_: AgentState, config: RunnableConfig):
    thread_id = config["configurable"]["thread_id"]
    vfs = get_vfs()
    content = vfs.readtext(f"todos_{thread_id}.json")

    todos = json.loads(content)
    task = get_next_todo(todos)

    if task is None:
        return "done"

    return Send("research", {"task": task})

def route(state: AgentState):
    return state["action"]

deep_researcher_builder = StateGraph(AgentState)

tools_list = [write_todos, completed_task]

deep_researcher_builder.add_node("planning", planning_node)
deep_researcher_builder.add_node("research", research_node)
deep_researcher_builder.add_node("tools", ToolNode(tools_list, messages_key="tmp_messages"))
deep_researcher_builder.add_node("synthesis", synthesis_node)
deep_researcher_builder.add_node("verification", verification_node)
deep_researcher_builder.add_node("finalize", finalize_node)
deep_researcher_builder.add_node("gatekeeper", gatekeeper_node)

# deep_researcher_builder.set_entry_point("planning")
deep_researcher_builder.set_entry_point("gatekeeper")
deep_researcher_builder.add_conditional_edges(
    "gatekeeper",
    route,
    {"refuse": END, "ask_user": END, "proceed": "planning"},
)
deep_researcher_builder.add_edge("planning", "tools")

deep_researcher_builder.add_conditional_edges(
    "tools",
    assign_task,
    {"done": "synthesis", "research": "research"},
)

deep_researcher_builder.add_edge("research", "tools")
deep_researcher_builder.add_edge("synthesis", "verification")
deep_researcher_builder.add_conditional_edges(
    "verification",
    partial(tools_condition, messages_key="tmp_messages"),
    {"tools": "tools", END: "finalize"},
)

deep_researcher = deep_researcher_builder.compile()
