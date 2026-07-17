from dataclasses import dataclass
from typing import Annotated, Literal, Optional, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph import MessagesState

from app.schemas.todo import Todo


class AgentState(MessagesState):
    query: Optional[str]
    todos: list[Todo]
    retries_time: int
    orchestrator_messages: list[AnyMessage]
    execution_id: str


class GuardState(AgentState):
    action: Optional[Literal["refuse", "ask_user", "proceed"]]


class GatekeeperOutput(TypedDict):
    """Structured output from the gatekeeper node after safety check, clarity check, and query enhancement.

    This model captures the three possible outcomes:
    - refuse: the query is unsafe or violates policy.
    - ask_user: the query is safe but unclear; specific clarification questions are asked.
    - proceed: the query is both safe and clear; a refined, enhanced query is provided for the planner.
    """

    action: Annotated[
        Literal["refuse", "ask_user", "proceed"],
        "The decision after safety and clarity checks.",
    ]
    message: Annotated[
        Optional[str],
        "Refusal message, clarification questions or clarified query to show to the user, None if proceed.",
    ]
    query: Annotated[
        Optional[str], "If proceed, the fully clarified query to pass to planner."
    ]


@dataclass
class AgentContext:
    reason_model_name: Optional[str] = None
    chat_model_name: Optional[str] = None


class SearchWorkerState(TypedDict):
    task: str
    execution_id: str


class SearcherState(MessagesState):
    execution_id: str
