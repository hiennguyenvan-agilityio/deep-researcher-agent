from typing import Annotated, Literal, Optional, TypedDict

from langgraph.graph import MessagesState

from app.core.langgraph.tools.todo import Todo


class AgentState(MessagesState):
    query: Optional[str]
    action: Optional[Literal["refuse", "ask_user", "proceed"]]


class ResearchAgentState(MessagesState):
    query: str
    step: int
    todos: list[Todo]


class SearchAgentState(MessagesState):
    task: str


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
