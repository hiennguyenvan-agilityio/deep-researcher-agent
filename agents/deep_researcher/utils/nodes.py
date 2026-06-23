import uuid

from click import Command
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from agents.deep_researcher.prompts import GATEKEEPER_PROMPT, PLANNER_PROMPT, RESERACHER_PROMPT, SYSTHESIS_PROMPT, VERIFICATION_PROMPT
from agents.deep_researcher.utils.states import AgentState, WorkerState
from agents.deep_researcher.utils.structuted_outputs import GatekeeperOutput
from resources.vitual_file_system import get_vfs
from tools.todo import write_todos
from utils.common import get_text_from_llm_response


def gatekeeper_node(state: AgentState):
    """Perform safety/clarity/enhancement check and return structured decision."""

    llm = init_chat_model(
        model="google_genai:gemini-3.1-flash-lite-preview"
    ).with_structured_output(GatekeeperOutput)

    prompt = ChatPromptTemplate([
        ("system", GATEKEEPER_PROMPT),
        ("placeholder", "{messages}"),
    ])

    chain = prompt | llm
    response = chain.invoke(state)

    action = response.get("action")

    if(action == "proceed"):
        query = response.get("query")

        return {"query": query, "action": action}
    
    message = response.get("message")

    return {"messages": AIMessage(content=message), "action": action}

def planning_node(state: AgentState):
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

    return {
        "tmp_messages": [response]
    }


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

    return Command(
        update={
            "tmp_messages": [AIMessage(content="", tool_calls=[tool_call])]
        }
    )

def synthesis_node(state: AgentState, config: RunnableConfig):
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

def verification_node(state: AgentState, config: RunnableConfig):
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

    return {"tmp_messages": [response]}

def finalize_node(state: AgentState):
    message = state["tmp_messages"]

    return {"messages": message}