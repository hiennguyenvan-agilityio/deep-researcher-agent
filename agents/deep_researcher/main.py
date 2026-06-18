import json
from typing import TypedDict
import uuid

from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.runnables import RunnableConfig
from langgraph.types import Send

from agents.deep_researcher.prompts import PLANNER_SYSTEM_PROMPT, RESERACHER_PROMPT
from resources.backend import get_filesystem_backend
from tools.todo import Todo, completed_task, write_todos
from utils.common import get_next_todo


class WorkerState(TypedDict):
    task: Todo

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

def assign_task(_: MessagesState, config: RunnableConfig):
    fileSystemBackend = get_filesystem_backend()
    thread_id = config["configurable"]["thread_id"]

    read_result = fileSystemBackend.read(f"todos_{thread_id}.json")
    content = read_result.file_data["content"]
    todos = json.loads(content)

    task = get_next_todo(todos)

    if(task is None):
        return "done"

    return Send("research", {"task": task})

def research_node(state: WorkerState):
    llm = init_chat_model(model="google_genai:gemini-3.1-flash-lite-preview")

    task = state["task"]
    
    prompt = ChatPromptTemplate(
        [
            ("human", RESERACHER_PROMPT)
        ]
    )

    chain = prompt | llm

    response = chain.invoke({"task": task["content"]})

    tool_call = {
        "name": "completed_task",
        "args": {"todo": task},
        "id": str(uuid.uuid4()),
        "type": "tool_call",
    }

    return {"messages": [response, AIMessage(content="", tool_calls=[tool_call])]}

def synthesis_node(state: MessagesState):
    return "Coming soon..."

def verification_node():
    return "Coming soon..."

def finalize_node():
    return "Coming soon..."

def should_continue_after_verify():
    return "Coming soon..."

deep_researcher_builder = StateGraph(MessagesState)

tools_list = [write_todos, completed_task]

deep_researcher_builder.add_node("planning", planning_node)
deep_researcher_builder.add_node("research", research_node)
deep_researcher_builder.add_node("tools", ToolNode(tools_list))
deep_researcher_builder.add_node("synthesis", synthesis_node)
deep_researcher_builder.add_node("verification", verification_node)
deep_researcher_builder.add_node("finalize", finalize_node)

deep_researcher_builder.set_entry_point("planning")
deep_researcher_builder.add_edge("planning", "tools")

deep_researcher_builder.add_conditional_edges(
    "tools",
    assign_task,
    {"done": "synthesis", "research": "research"},
)

deep_researcher_builder.add_edge("research", "tools")
deep_researcher_builder.add_edge("synthesis", "verification")
deep_researcher_builder.add_conditional_edges("verification", should_continue_after_verify, {"finalize": "finalize", "fix": "research"})

deep_researcher = deep_researcher_builder.compile()