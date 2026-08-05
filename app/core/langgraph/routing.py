import uuid

from langgraph.prebuilt import tools_condition
from langgraph.types import Send
from langchain_core.callbacks.manager import adispatch_custom_event

from app.schemas.graph import AgentState


async def orchestrator_tools_condition(state: AgentState):
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
