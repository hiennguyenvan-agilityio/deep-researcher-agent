from typing import Literal, Optional

from langgraph.graph import MessagesState


class GuardState(MessagesState):
    query: Optional[str]
    action: Optional[Literal["refuse", "ask_user", "proceed"]]
