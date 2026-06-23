from langgraph.graph import MessagesState


class PlannerAgentState(MessagesState):
    query: str