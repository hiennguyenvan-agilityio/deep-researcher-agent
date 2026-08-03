# from dataclasses import dataclass
import operator
from typing import Annotated, Literal, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph import MessagesState, add_messages
from pydantic import BaseModel, Field

from app.core.utils.common import merge_todos
from app.schemas.todo import Todo


class AgentState(MessagesState):
    todos: Annotated[list[Todo], merge_todos]
    loop_count: int
    orchestrator_messages: Annotated[list[AnyMessage], add_messages]
    execution_id: str
    sanitized_messages: Annotated[dict[int, AnyMessage], operator.or_]


class AgentOutput(MessagesState):
    execution_id: str


class AgentContext(BaseModel):
    reason_model_name: str | None = None
    chat_model_name: str | None = None
    token_limit: int | None = None


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
