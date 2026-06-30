import os

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

from agents.researcher.prompts import PLANNER_PROMPT, SYSTHESIS_PROMPT
from agents.researcher.utils.states import ResearchAgentState, WorkerState
from agents.researcher.utils.tools import write_todos
from resources.models import get_reason_model
from resources.vitual_file_system import get_vfs
from utils.common import get_text_from_llm_response
from agents.worker.main import worker_agent
from langchain_core.runnables import RunnableConfig


def orchestrator(state: ResearchAgentState, config: RunnableConfig):
    """Orchestrator that generates a plan for the researcher"""

    # llm = get_reason_model().bind_tools([write_todos])
    model_name = os.getenv("REASON_MODEL_NAME")
    llm = init_chat_model(model=model_name, temperature=0).bind_tools([write_todos])

    thread_id = config["configurable"]["thread_id"]
    vfs = get_vfs()

    research_node_path = f"research_note_{thread_id}.txt"

    research_notes = None

    if vfs.exists(research_node_path):
        research_notes = vfs.readtext(research_node_path)

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


def worker(state: WorkerState, config: RunnableConfig):
    """"""

    task = state["task"]
    response = worker_agent.invoke({"task": task["content"]})

    ai_response_text = get_text_from_llm_response(response["messages"][-1])
    content = "------------------\n" f"{ai_response_text}\n" "\n"

    # Write research note to VFS
    thread_id = config["configurable"]["thread_id"]
    research_node_path = f"research_note_{thread_id}.txt"
    vfs = get_vfs()

    vfs.appendtext(research_node_path, content)

    # completed_task(task, thread_id)

    return


def synthesizer(state: ResearchAgentState, config: RunnableConfig):
    thread_id = config["configurable"]["thread_id"]
    vfs = get_vfs()

    research_node_path = f"research_note_{thread_id}.txt"

    research_note = vfs.readtext(research_node_path)

    llm = get_reason_model()

    prompt = ChatPromptTemplate(
        [
            ("system", SYSTHESIS_PROMPT),
            ("human", "{query}"),
        ]
    )

    chain = prompt | llm

    response = chain.invoke({"query": state["query"], "research_note": research_note})

    return {"messages": response}
