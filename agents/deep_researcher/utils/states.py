from typing import Literal, Optional, TypedDict

from langgraph.graph import MessagesState


class GuardState(MessagesState):
    query: Optional[str]
    action: Optional[Literal["refuse", "ask_user", "proceed"]]


class ReviewState(MessagesState):
    query: Optional[str]
    approved: bool
