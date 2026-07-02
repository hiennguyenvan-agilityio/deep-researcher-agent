import os

from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from app.core.langgraph.tools.todo import write_todos
from app.core.prompts import GATEKEEPER_PROMPT, PLANNER_PROMPT, SYNTHESIS_PROMPT
from app.core.services.file_system import get_fs
from app.core.services.llm import get_reason_model
from app.core.utils.llm import get_text_from_llm_response
from app.schemas.graph import AgentState, GatekeeperOutput
from app.core.langgraph.researcher.graph import researcher_agent
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


def orchestrator(state: AgentState, config: RunnableConfig):
    """Orchestrator that generates a plan for the researcher"""

    # llm = get_reason_model().bind_tools([write_todos])
    model_name = os.getenv("REASON_MODEL_NAME")
    llm = init_chat_model(model=model_name, temperature=0).bind_tools([write_todos])

    thread_id = config["configurable"]["thread_id"]
    fs = get_fs()

    research_node_path = f"research_note_{thread_id}.txt"

    research_notes = None

    if fs.exists(research_node_path):
        research_notes = fs.readtext(research_node_path)

    prompt = ChatPromptTemplate(
        [
            ("system", PLANNER_PROMPT),
            ("human", "{query}"),
            ("placeholder", "{messages}"),
        ]
    )

    chain = prompt | llm
    response = chain.invoke(
        {
            "query": state["query"],
            "messages": state["messages"],
            "research_notes": research_notes,
        }
    )

    return {"messages": response, "step": state.get("step", 0) + 1}


def researcher(task: str, config: RunnableConfig):
    """"""

    response = researcher_agent.invoke({"task": task})

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


def verifier():
    return
