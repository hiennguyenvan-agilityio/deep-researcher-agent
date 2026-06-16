from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph

def orchestrator():
    return "Coming soon..."

def assign_workers():
    return "Coming soon..."

def clarifier():
    return "Coming soon..."

def researcher():
    return "Coming soon..."

def summarizer():
    return "Coming soon..."

def reviewer():
    return "Coming soon..."

def decision():
    return "Coming soon..."

deep_researcher_builder = StateGraph(MessagesState)

deep_researcher_builder.add_node("orchestrator", orchestrator)
deep_researcher_builder.add_node("clarifier", clarifier)
deep_researcher_builder.add_node("researcher", researcher)
deep_researcher_builder.add_node("summarizer", summarizer)
deep_researcher_builder.add_node("reviewer", reviewer)

deep_researcher_builder.add_edge(START, "orchestrator")
deep_researcher_builder.add_conditional_edges(
    "orchestrator", assign_workers, ["clarifier", "researcher"]
)

deep_researcher_builder.add_edge("clarifier", "orchestrator")
deep_researcher_builder.add_edge("researcher", "summarizer")
deep_researcher_builder.add_edge("summarizer", "reviewer")
deep_researcher_builder.add_conditional_edges(
    "reviewer", decision, ["orchestrator", END]
)

deep_researcher = deep_researcher_builder.compile()