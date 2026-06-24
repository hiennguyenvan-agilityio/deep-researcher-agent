from typing import TypedDict

from langgraph.graph import MessagesState


class ResearchAgentState(MessagesState):
    query: str


class WorkerState(TypedDict):
    task: str
