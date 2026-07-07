from typing import Annotated, Literal, Optional, TypedDict

from langgraph.graph import MessagesState

from app.schemas.todo import Todo


class AgentState(MessagesState):
    query: Optional[str]
    step: int
    todos: list[Todo]
    planner_instruction: Optional[str]
    retries_time: int


class GuardState(AgentState):
    query: Optional[str]
    action: Optional[Literal["refuse", "ask_user", "proceed"]]


class VerifierState(AgentState):
    planner_instruction: Optional[str]
    action: Optional[Literal["approved", "next_research", "replan"]]


class ResearchAgentState(MessagesState):
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


class VerifierOutput(TypedDict):
    """Decision returned by the Research Verifier."""

    decision: Literal["approved", "next_research", "replan"]
    """The next action for the workflow."""

    reason: str
    """A concise explanation for the decision."""

    planner_instruction: str | None
    """
    Instructions for the Planner
    When decision == "replan". Otherwise, this field should be None.

    Describe how the research plan should be updated. For example:
    - which pending tasks should be rewritten,
    - what newly discovered context should be incorporated,
    - what new research tasks should be added,
    - which tasks are no longer necessary.
    """
