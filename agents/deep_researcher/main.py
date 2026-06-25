import os

from dotenv import load_dotenv
from langgraph.graph import END, MessagesState, StateGraph

from agents.deep_researcher.utils.nodes import gatekeeper, researcher, reviewer
from agents.deep_researcher.utils.states import ReviewState, GuardState
from resources.models import initialise_chat_model, initialise_reason_model

load_dotenv()


def route(state: GuardState):
    return state["action"]


def review_route(state: ReviewState):
    if state["approved"]:
        return END

    return "researcher"


reason_model_name = os.getenv("REASON_MODEL_NAME")
chat_model_name = os.getenv("CHAT_MODEL_NAME")

initialise_reason_model(reason_model_name)
initialise_chat_model(chat_model_name)

deep_researcher_builder = StateGraph(MessagesState)

deep_researcher_builder.add_node("gatekeeper", gatekeeper)
deep_researcher_builder.add_node("researcher", researcher)
deep_researcher_builder.add_node("reviewer", reviewer)

deep_researcher_builder.set_entry_point("gatekeeper")
deep_researcher_builder.add_conditional_edges(
    "gatekeeper",
    route,
    {"refuse": END, "ask_user": END, "proceed": "researcher"},
)

deep_researcher_builder.add_edge("researcher", "reviewer")
deep_researcher_builder.add_edge("reviewer", END)

deep_researcher_builder.add_conditional_edges(
    "reviewer",
    review_route,
    {END: END, "researcher": "researcher"},
)

deep_researcher_agent = deep_researcher_builder.compile()
