from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agents.deep_researcher.prompts import PLANNER_SYSTEM_PROMPT
from tools.todo import write_todos

def planning_node(state: MessagesState):
    """Orchestrator that generates a plan for the researcher"""

    # planner = init_chat_model(model="gpt-5.1").bind_tools([write_todos])
    planner = init_chat_model(model="google_genai:gemini-3.1-flash-lite-preview").bind_tools([write_todos])

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            ("placeholder", "{messages}"),
        ]
    )

    chain = prompt | planner

    response = chain.invoke(state)
    
    return {"messages": response}

def research_node():
    return "Coming soon..."

def clarify():
    return "Coming soon..."

def verification_node():
    return "Coming soon..."

def finalize_node():
    return "Coming soon..."

def should_continue_execution():
    return "Coming soon..."

def should_continue_after_verify():
    return "Coming soon..."

deep_researcher_builder = StateGraph(MessagesState)

tools_list = [write_todos]

deep_researcher_builder.add_node("planning", planning_node)
deep_researcher_builder.add_node("research", research_node)
deep_researcher_builder.add_node("tools", ToolNode(tools_list))
deep_researcher_builder.add_node("verification", verification_node)
deep_researcher_builder.add_node("finalize", finalize_node)

deep_researcher_builder.add_edge(START, "planning")
deep_researcher_builder.add_conditional_edges(
    "planning",
    tools_condition,
    {END: "research", "tools": "tools"},
)

deep_researcher_builder.add_edge("planning", "research")
deep_researcher_builder.add_conditional_edges("research", should_continue_execution, {"tools": "tools", "verification": "verification"})
deep_researcher_builder.add_edge("tools", "research")
deep_researcher_builder.add_conditional_edges("verification", should_continue_after_verify, {"finalize": "finalize", "fix": "research"})

deep_researcher = deep_researcher_builder.compile()