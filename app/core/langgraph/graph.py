from typing import Optional

from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Checkpointer, Send

from app.core.langgraph.nodes import (
    gatekeeper,
    orchestrator,
    searcher,
    synthesizer,
)
from app.core.langgraph.tools.todo import write_todos
from app.core.services.llm import initialise_chat_model, initialise_reason_model
from app.schemas.graph import AgentState, GuardState


def get_tasks(todos, step):
    """Get tasks for the current step"""
    return [
        todo for todo in todos if todo["step"] == step and todo["status"] != "completed"
    ]


def route(state: GuardState):
    return state["action"]


def assign_workers(state: AgentState):
    """Assign a worker to each task in todo list"""

    pending_todos = [todo for todo in state["todos"] if todo["status"] == "pending"]

    return [Send("searcher", task["content"]) for task in pending_todos]


async def get_graph(
    chat_model_name: str,
    reason_model_name: Optional[str] = None,
    checkpointer: Optional[Checkpointer] = None,
):
    initialise_chat_model(chat_model_name)
    initialise_reason_model(reason_model_name or chat_model_name)

    deep_researcher_builder = StateGraph(
        AgentState, input_schema=MessagesState, output_schema=MessagesState
    )

    deep_researcher_builder.add_node("gatekeeper", gatekeeper)
    tools_list = [write_todos]
    deep_researcher_builder.add_node("tools", ToolNode(tools_list))
    deep_researcher_builder.add_node("orchestrator", orchestrator)
    deep_researcher_builder.add_node("searcher", searcher)
    deep_researcher_builder.add_node("synthesizer", synthesizer)

    deep_researcher_builder.set_entry_point("gatekeeper")
    deep_researcher_builder.add_conditional_edges(
        "gatekeeper",
        route,
        {"refuse": END, "ask_user": END, "proceed": "orchestrator"},
    )
    deep_researcher_builder.add_conditional_edges(
        "orchestrator",
        tools_condition,
        {"tools": "tools", END: "synthesizer"},
    )
    deep_researcher_builder.add_conditional_edges("tools", assign_workers, ["searcher"])
    deep_researcher_builder.add_edge("searcher", "orchestrator")
    deep_researcher_builder.add_edge("synthesizer", END)

    deep_researcher_agent = deep_researcher_builder.compile(checkpointer=checkpointer)

    return deep_researcher_agent
