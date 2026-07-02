import json

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Send

from app.core.langgraph.researcher.nodes import orchestrator, synthesizer, worker
from app.core.langgraph.tools.todo import write_todos
from app.core.services.file_system import get_fs
from app.schemas.graph import ResearchAgentState


def assign_workers(state: ResearchAgentState, config: RunnableConfig):
    """Assign a worker to each task in todo list"""

    thread_id = config["configurable"]["thread_id"]
    fs = get_fs()
    content = fs.readtext(f"todos_{thread_id}.json")
    current_step = state.get("step")

    todos = json.loads(content)

    tasks = [
        todo
        for todo in todos
        if todo["step"] == current_step and todo["status"] != "completed"
    ]

    if not tasks:
        return "synthesizer"

    return [Send("worker", {"task": task}) for task in tasks]


researcher_builder = StateGraph(ResearchAgentState)

tools_list = [write_todos]

researcher_builder.add_node("orchestrator", orchestrator)
researcher_builder.add_node("tools", ToolNode(tools_list))
researcher_builder.add_node("worker", worker)
researcher_builder.add_node("synthesizer", synthesizer)

researcher_builder.set_entry_point("orchestrator")

researcher_builder.add_edge("orchestrator", "tools")

researcher_builder.add_conditional_edges(
    "tools", assign_workers, ["worker", "synthesizer"]
)
researcher_builder.add_edge("worker", "orchestrator")
researcher_builder.add_edge("synthesizer", END)

researcher_agent = researcher_builder.compile()
