import os

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command

from app.core.langgraph.tools.mcp import load_researcher_tools
from app.core.langgraph.tools.research_note import write_research_notes
from app.core.langgraph.tools.todo import write_todos
from app.core.prompts import (
    GATEKEEPER_PROMPT,
    ORCHESTRATOR_PROMPT,
    SEARCHER_PROMPT,
    SYNTHESIS_PROMPT,
)
from app.core.services.file_system import get_fs
from app.core.services.llm import get_reason_model
from app.schemas.graph import (
    AgentState,
    GatekeeperOutput,
)
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

    retries_time = state.get("retries_time", -1) + 1

    if retries_time > int(os.getenv("MAX_RETRIES", 5)):
        return Command(goto="systhesis")

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

    prompt = ChatPromptTemplate(
        [
            ("system", ORCHESTRATOR_PROMPT),
            ("human", "{query}"),
        ]
    )

    chain = prompt | llm
    response = chain.invoke(
        {
            "query": state["query"],
            "research_notes": research_notes,
        }
    )

    return {"messages": response, "retries_time": retries_time}


async def searcher(task: str):
    """"""

    model_name = os.getenv("CHAT_MODEL_NAME")
    search_platform = os.getenv("SEARCH_PLATFORM", "exa")
    tools = await load_researcher_tools(search_platform=search_platform)
    tools.append(write_research_notes)
    search_agent = create_agent(model_name, tools=tools, system_prompt=SEARCHER_PROMPT)

    await search_agent.ainvoke({"messages": [("human", task)]})

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
