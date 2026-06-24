from langgraph.graph import MessagesState


class SearchAgentState(MessagesState):
    task: str
