from typing import Annotated, Literal, Optional, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph import MessagesState, add_messages

class AgentState(MessagesState):
    tmp_messages: Optional[Annotated[list[AnyMessage], add_messages]]
    query: Optional[str]
    action: Optional[Literal["refuse", "ask_user", "proceed"]]

class WorkerState(MessagesState):
    task: str