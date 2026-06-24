import json

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Send

from agents.researcher.utils.nodes import orchestrator, worker, synthesizer
from agents.researcher.utils.states import ResearchAgentState
from resources.vitual_file_system import get_vfs
from tools.todo import write_todos


def assign_workers(_: ResearchAgentState, config: RunnableConfig):
    """Assign a worker to each task in todo list"""

    thread_id = config["configurable"]["thread_id"]
    vfs = get_vfs()
    content = vfs.readtext(f"todos_{thread_id}.json")

    todos = json.loads(content)

    return [Send("worker", {"task": task}) for task in todos]


researcher_builder = StateGraph(ResearchAgentState)

tools_list = [write_todos]

researcher_builder.add_node("orchestrator", orchestrator)
researcher_builder.add_node("tools", ToolNode(tools_list))
researcher_builder.add_node("worker", worker)
researcher_builder.add_node("synthesizer", synthesizer)

researcher_builder.set_entry_point("orchestrator")

researcher_builder.add_edge("orchestrator", "tools")

researcher_builder.add_conditional_edges("tools", assign_workers, ["worker"])
researcher_builder.add_edge("worker", "synthesizer")
researcher_builder.add_edge("synthesizer", END)

researcher_agent = researcher_builder.compile()
