from typing import Optional

from langgraph.graph import END, MessagesState, StateGraph
from langgraph.types import Checkpointer

from agents.deep_researcher.utils.nodes import gatekeeper, researcher
from agents.deep_researcher.utils.states import GuardState
from resources.models import initialise_chat_model, initialise_reason_model


def route(state: GuardState):
    return state["action"]


def get_deep_researcher_agent(
    chat_model_name: str,
    reason_model_name: Optional[str] = None,
    checkpointer: Optional[Checkpointer] = None,
):
    initialise_chat_model(chat_model_name)
    initialise_reason_model(reason_model_name or chat_model_name)

    deep_researcher_builder = StateGraph(MessagesState)

    deep_researcher_builder.add_node("gatekeeper", gatekeeper)
    deep_researcher_builder.add_node("researcher", researcher)

    deep_researcher_builder.set_entry_point("gatekeeper")
    deep_researcher_builder.add_conditional_edges(
        "gatekeeper",
        route,
        {"refuse": END, "ask_user": END, "proceed": "researcher"},
    )

    deep_researcher_builder.add_edge("researcher", END)

    deep_researcher_agent = deep_researcher_builder.compile(checkpointer=checkpointer)

    return deep_researcher_agent
