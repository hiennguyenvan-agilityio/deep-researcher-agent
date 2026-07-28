# from dataclasses import dataclass
from typing import Annotated, Literal, Optional, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph import MessagesState, add_messages
from pydantic import BaseModel, Field

from app.core.utils.common import merge_todos
from app.schemas.todo import Todo


class AgentState(MessagesState):
    query: Optional[str]
    todos: Annotated[list[Todo], merge_todos]
    loop_count: int
    orchestrator_messages: Annotated[list[AnyMessage], add_messages]
    execution_id: str


class AgentOutput(MessagesState):
    execution_id: str


class GuardState(AgentState):
    action: Optional[Literal["refuse", "ask_user", "proceed"]]


class GatekeeperOutput(BaseModel):
    """Structured output from the gatekeeper node after safety check, clarity check, and query enhancement.

    This model captures the three possible outcomes:
    - refuse: the query is unsafe or violates policy.
    - ask_user: the query is safe but unclear; specific clarification questions are asked.
    - proceed: the query is both safe and clear; a refined, enhanced query is provided for the planner.
    """

    action: Literal["refuse", "ask_user", "proceed"] = Field(
        description="The decision after safety and clarity checks."
    )
    message: Optional[str] = Field(
        description="Refusal message, clarification questions or clarified query to show to the user, None if proceed."
    )
    query: Optional[str] = Field(
        description="If proceed, the fully clarified query to pass to planner."
    )


class AgentContext(BaseModel):
    reason_model_name: str | None = None
    chat_model_name: str | None = None


class SearchWorkerState(TypedDict):
    task: str
    execution_id: str


class SearcherState(MessagesState):
    execution_id: str


class SearcherOutput(BaseModel):
    status: Literal["failed", "completed"] = Field(
        description=(
            "'completed' only after successfully calling the "
            "`write_research_notes` tool to save the research findings successfully. "
            "Use 'failed' if the research task could not be completed or "
            "the findings could not be saved."
        )
    )
