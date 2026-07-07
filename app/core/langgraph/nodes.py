import os

from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from app.core.langgraph.tools.todo import write_todos
from app.core.prompts import (
    GATEKEEPER_PROMPT,
    PLANNER_PROMPT,
    REPLAN_INTRO,
    SYNTHESIS_PROMPT,
    VERIFIER_PROMPT,
)
from app.core.services.file_system import get_fs
from app.core.services.llm import get_chat_model, get_reason_model
from app.core.utils.llm import get_text_from_llm_response
from app.schemas.graph import (
    AgentState,
    GatekeeperOutput,
    VerifierOutput,
    VerifierState,
)
from app.core.langgraph.researcher.graph import get_graph as get_researcher_agent
from langchain_core.runnables import RunnableConfig


def gatekeeper(state: AgentState):
    """Perform safety/clarity/enhancement check and return structured decision."""

    llm = get_reason_model().with_structured_output(GatekeeperOutput)

    prompt = ChatPromptTemplate(
        [
            ("system", GATEKEEPER_PROMPT),
            ("placeholder", "{messages}"),
        ]
    )

    chain = prompt | llm
    response = chain.invoke(state)

    action = response.get("action")

    if action == "proceed":
        query = response.get("query")

        return {"query": query, "action": action}

    message = response.get("message")

    return {"messages": AIMessage(content=message), "action": action}


async def orchestrator(state: AgentState, config: RunnableConfig):
    """Orchestrator that generates a plan for the researcher"""

    # llm = get_reason_model().bind_tools([write_todos])
    model_name = os.getenv("REASON_MODEL_NAME")
    tools = [write_todos]
    llm = init_chat_model(model=model_name, temperature=0).bind_tools(tools)

    thread_id = config["configurable"]["thread_id"]
    fs = get_fs()

    research_node_path = f"research_note_{thread_id}.txt"

    research_notes = None

    if fs.exists(research_node_path):
        research_notes = fs.readtext(research_node_path)

    planner_instruction = state.get("planner_instruction")
    retries_time = state.get("retries_time", -1) + 1

    system_prompt = PLANNER_PROMPT + (REPLAN_INTRO if retries_time > 0 else "")

    prompt = ChatPromptTemplate(
        [
            ("system", system_prompt),
            ("human", "{query}"),
        ]
    )

    chain = prompt | llm
    response = chain.invoke(
        {
            "query": state["query"],
            "research_notes": research_notes,
            "planner_instruction": planner_instruction,
            "todos": state.get("todos"),
        }
    )

    return {"messages": response, "retries_time": retries_time}


async def researcher(task: str, config: RunnableConfig):
    """"""

    researcher_agent = await get_researcher_agent()

    response = await researcher_agent.ainvoke({"task": task})

    ai_response_text = get_text_from_llm_response(response["messages"][-1])
    content = f"------------------\n{ai_response_text}\n\n"

    # Write research note to fs
    thread_id = config["configurable"]["thread_id"]
    research_node_path = f"research_note_{thread_id}.txt"
    fs = get_fs()

    fs.appendtext(research_node_path, content)

    return


def synthesizer(state: AgentState, config: RunnableConfig):
    thread_id = config["configurable"]["thread_id"]
    fs = get_fs()

    research_node_path = f"research_note_{thread_id}.txt"

    research_note = fs.readtext(research_node_path)

    llm = get_reason_model()

    prompt = ChatPromptTemplate(
        [
            ("system", SYNTHESIS_PROMPT),
            ("human", "{query}"),
        ]
    )

    chain = prompt | llm

    response = chain.invoke({"query": state["query"], "research_note": research_note})

    return {"messages": response}


def verifier(state: AgentState, config: RunnableConfig) -> VerifierState:
    thread_id = config["configurable"]["thread_id"]
    fs = get_fs()

    research_nodes_path = f"research_note_{thread_id}.txt"

    research_notes = fs.readtext(research_nodes_path)

    llm = get_chat_model().with_structured_output(VerifierOutput)

    todos = state.get("todos")
    current_step = state.get("step", 1)

    updated_todos = [
        {
            **todo,
            "status": "completed" if todo["step"] == current_step else todo["status"],
        }
        for todo in todos
    ]

    prompt = ChatPromptTemplate(
        [
            ("system", VERIFIER_PROMPT),
            ("human", "{query}"),
        ]
    )

    chain = prompt | llm

    response = chain.invoke(
        {
            "query": state["query"],
            "research_notes": research_notes,
            "todos": updated_todos,
        }
    )

    return {
        "step": current_step + 1,
        "todos": updated_todos,
        "action": response["decision"],
        "planner_instruction": response["planner_instruction"],
    }
