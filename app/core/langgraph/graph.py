from typing import Optional

from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Checkpointer, Send

from app.core.langgraph.nodes import (
    gatekeeper,
    orchestrator,
    synthesizer,
    verifier,
    researcher,
)
from app.core.langgraph.tools.todo import write_todos
from app.core.services.llm import initialise_chat_model, initialise_reason_model
from app.schemas.graph import AgentState, GuardState, VerifierState


def get_tasks(todos, step):
    """Get tasks for the current step"""
    return [
        todo for todo in todos if todo["step"] == step and todo["status"] != "completed"
    ]


def route(state: GuardState):
    return state["action"]


def assign_workers(state: AgentState):
    """Assign a worker to each task in todo list"""

    todos = state.get("todos", [])
    current_step = state.get("step", 1)

    tasks = get_tasks(todos, current_step)

    if not tasks:
        return "synthesizer"

    return [Send("researcher", task["content"]) for task in tasks]


def verifier_route(state: VerifierState):
    action = state.get("action")

    todos = state.get("todos", [])
    current_step = state.get("step")
    retries_time = state.get("retries_time")

    if action == "next_research":
        tasks = get_tasks(todos, current_step)

        if not tasks:
            return "synthesizer"

        return [Send("researcher", task["content"]) for task in tasks]

    if action == "replan" and retries_time < 5:
        return "orchestrator"

    return "synthesizer"


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
    deep_researcher_builder.add_node("orchestrator", orchestrator)
    tools_list = [write_todos]
    deep_researcher_builder.add_node("tools", ToolNode(tools_list))
    deep_researcher_builder.add_node("researcher", researcher)
    deep_researcher_builder.add_node("synthesizer", synthesizer)
    deep_researcher_builder.add_node("verifier", verifier)

    deep_researcher_builder.set_entry_point("gatekeeper")
    deep_researcher_builder.add_conditional_edges(
        "gatekeeper",
        route,
        {"refuse": END, "ask_user": END, "proceed": "orchestrator"},
    )

    deep_researcher_builder.add_edge("orchestrator", "tools")

    deep_researcher_builder.add_conditional_edges(
        "tools", assign_workers, ["researcher", "synthesizer"]
    )
    deep_researcher_builder.add_edge("researcher", "verifier")
    deep_researcher_builder.add_conditional_edges(
        "verifier", verifier_route, ["researcher", "orchestrator", "synthesizer"]
    )
    deep_researcher_builder.add_edge("synthesizer", END)

    deep_researcher_agent = deep_researcher_builder.compile(checkpointer=checkpointer)

    return deep_researcher_agent
