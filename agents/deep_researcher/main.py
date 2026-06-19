import json
from typing import TypedDict
import uuid

from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.runnables import RunnableConfig
from langgraph.types import Send

from agents.deep_researcher.prompts import PLANNER_PROMPT, RESERACHER_PROMPT, SYSTHESIS_PROMPT, VERIFICATION_PROMPT
from resources.vitual_file_system import get_vfs
from tools.todo import Todo, completed_task, write_todos
from utils.common import get_next_todo, get_text_from_llm_response


class WorkerState(TypedDict):
    task: Todo

def planning_node(state: MessagesState):
    """Orchestrator that generates a plan for the researcher"""

    # planner = init_chat_model(model="gpt-5.1").bind_tools([write_todos])
    planner = init_chat_model(
        model="google_genai:gemini-3.1-flash-lite-preview"
    ).bind_tools([write_todos])

    prompt = ChatPromptTemplate([
        ("system", PLANNER_PROMPT),
        ("placeholder", "{messages}"),
    ])

    chain = prompt | planner
    response = chain.invoke(state)

    return {"messages": response}

def assign_task(_: MessagesState, config: RunnableConfig):
    thread_id = config["configurable"]["thread_id"]
    vfs = get_vfs()
    content = vfs.readtext(f"todos_{thread_id}.json")

    todos = json.loads(content)
    task = get_next_todo(todos)

    if task is None:
        return "done"

    return Send("research", {"task": task})


def research_node(state: WorkerState, config: RunnableConfig):
    llm = init_chat_model(model="google_genai:gemini-3.1-flash-lite-preview")

    task = state["task"]

    prompt = ChatPromptTemplate([("human", RESERACHER_PROMPT)])

    chain = prompt | llm
    response = chain.invoke({"task": task["content"]})

    ai_response_text = get_text_from_llm_response(response)
    content = (
        "------------------\n"
        f"{ai_response_text}\n"
        "\n"
    )

    # Write research note to VFS
    thread_id = config["configurable"]["thread_id"]
    research_node_path = f"research_note_{thread_id}.txt"
    vfs = get_vfs()
    
    vfs.appendtext(research_node_path, content)

    tool_call = {
        "name": "completed_task",
        "args": {"todo": task},
        "id": str(uuid.uuid4()),
        "type": "tool_call",
    }

    return {"messages": [AIMessage(content="", tool_calls=[tool_call])]}

def synthesis_node(state: MessagesState, config: RunnableConfig):
    thread_id = config["configurable"]["thread_id"]
    research_node_path = f"research_note_{thread_id}.txt"
    vfs = get_vfs()

    research_note = vfs.readtext(research_node_path)

    llm = init_chat_model(model="google_genai:gemini-3.1-flash-lite-preview")

    prompt = ChatPromptTemplate([
        ("system", SYSTHESIS_PROMPT),
        ("placeholder", "{messages}"),
    ])

    chain = prompt | llm

    response = chain.invoke({"messages": state["messages"], "research_note": research_note})

    ai_response_text = get_text_from_llm_response(response)

    vfs = get_vfs()
    vfs.writetext(f"systhesis_{thread_id}.txt", ai_response_text)

    return

def verification_node(state: MessagesState, config: RunnableConfig):
    thread_id = config["configurable"]["thread_id"]
    llm = init_chat_model(model="google_genai:gemini-3.1-flash-lite-preview").bind_tools([write_todos])
    vfs = get_vfs()
    ai_response = vfs.readtext(f"systhesis_{thread_id}.txt")

    prompt = ChatPromptTemplate([
        ("system", VERIFICATION_PROMPT),
        ("placeholder", "{messages}"),
    ])

    chain = prompt | llm

    response = chain.invoke({"messages": state["messages"], "ai_response": ai_response})

    print("final response", response)

    return {"messages": response}

deep_researcher_builder = StateGraph(MessagesState)

tools_list = [write_todos, completed_task]

deep_researcher_builder.add_node("planning", planning_node)
deep_researcher_builder.add_node("research", research_node)
deep_researcher_builder.add_node("tools", ToolNode(tools_list))
deep_researcher_builder.add_node("synthesis", synthesis_node)
deep_researcher_builder.add_node("verification", verification_node)

deep_researcher_builder.set_entry_point("planning")
deep_researcher_builder.add_edge("planning", "tools")

deep_researcher_builder.add_conditional_edges(
    "tools",
    assign_task,
    {"done": "synthesis", "research": "research"},
)

deep_researcher_builder.add_edge("research", "tools")
deep_researcher_builder.add_edge("synthesis", "verification")
deep_researcher_builder.add_conditional_edges(
    "verification",
    tools_condition,
    {"tools": "tools", END: END},
)

deep_researcher = deep_researcher_builder.compile()
