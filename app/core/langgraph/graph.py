from typing import Optional
import uuid

from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Checkpointer, Send
from langchain_core.callbacks.manager import adispatch_custom_event

from app.core.langgraph.nodes import (
    feedback,
    gatekeeper,
    initial,
    orchestrator,
    searcher,
    synthesizer,
)
from app.core.langgraph.tools.todo import write_todos
from app.schemas.graph import AgentContext, AgentOutput, AgentState


async def orchestrator_tools_condition(state):
    return tools_condition(
        state,
        messages_key="orchestrator_messages",
    )


async def assign_workers(state: AgentState):
    """Assign a worker to each task in todo list"""
    await adispatch_custom_event(
        "manually_emit_message",
        {
            "message": "Searching...",
            "message_id": str(uuid.uuid4()),
            "role": "activity",
        },
    )

    pending_todos = [todo for todo in state["todos"] if todo["status"] == "pending"]

    return [
        Send(
            "searcher",
            {
                "task": task["content"],
                "execution_id": state["execution_id"],
            },
        )
        for task in pending_todos
    ]


async def get_graph(checkpointer: Optional[Checkpointer] = None):
    deep_researcher_builder = StateGraph(
        AgentState,
        input_schema=MessagesState,
        output_schema=AgentOutput,
        context_schema=AgentContext,
    )

    deep_researcher_builder.add_node("initial", initial)
    deep_researcher_builder.add_node("gatekeeper", gatekeeper)
    deep_researcher_builder.add_node("orchestrator", orchestrator)
    tools_list = [write_todos]
    deep_researcher_builder.add_node(
        "tools", ToolNode(tools_list, messages_key="orchestrator_messages")
    )
    deep_researcher_builder.add_node("searcher", searcher)
    deep_researcher_builder.add_node("synthesizer", synthesizer)
    deep_researcher_builder.add_node("feedback", feedback)

    deep_researcher_builder.set_entry_point("initial")
    deep_researcher_builder.add_edge("initial", "gatekeeper")

    deep_researcher_builder.add_conditional_edges(
        "orchestrator",
        orchestrator_tools_condition,
        {"tools": "tools", END: "synthesizer"},
    )
    deep_researcher_builder.add_conditional_edges("tools", assign_workers, ["searcher"])
    deep_researcher_builder.add_edge("searcher", "orchestrator")
    deep_researcher_builder.add_edge("synthesizer", "feedback")

    deep_researcher_agent = deep_researcher_builder.compile(checkpointer=checkpointer)

    return deep_researcher_agent
