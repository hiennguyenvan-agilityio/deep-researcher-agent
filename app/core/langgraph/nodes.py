import os

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command, interrupt
from langgraph.runtime import Runtime

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
from app.schemas.graph import (
    AgentContext,
    AgentState,
    GatekeeperOutput,
)


def gatekeeper(state: AgentState, runtime: Runtime[AgentContext]):
    """Perform safety/clarity/enhancement check and return structured decision."""

    context = runtime.context
    reason_model_name = getattr(context, "reason_model_name", None) or os.getenv(
        "REASON_MODEL_NAME"
    )

    llm = init_chat_model(reason_model_name).with_structured_output(GatekeeperOutput)

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


async def request_confirmation(state: AgentState):
    approved = interrupt(
        {
            "message": (
                "Please help review your request before I begin.\n"
                "\n"
                f"{state['query']}\n"
                "\n"
                "Click Approve to continue or Cancel to make changes."
            )
        }
    )

    if approved:
        return Command(goto="orchestrator")

    return Command(goto="orchestrator")


async def orchestrator(state: AgentState, runtime: Runtime[AgentContext]):
    """Orchestrator that generates a plan for the researcher"""

    retries_time = state.get("retries_time", -1) + 1

    if retries_time > int(os.getenv("MAX_RETRIES", 5)):
        return Command(goto="synthesizer")

    context = runtime.context
    model_name = getattr(context, "reason_model_name", None) or os.getenv(
        "REASON_MODEL_NAME"
    )
    tools = [write_todos]

    llm = init_chat_model(model=model_name, temperature=0).bind_tools(tools)

    thread_id = runtime.execution_info.thread_id
    run_id = runtime.context.run_id
    fs = get_fs()

    research_node_path = f"{thread_id}/research_note_{run_id}.txt"

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

    return {"orchestrator_messages": [response], "retries_time": retries_time}


async def searcher(task: str, runtime: Runtime[AgentContext]):
    """Execute a single search task."""

    context = runtime.context
    model_name = getattr(context, "reason_model_name", None) or os.getenv(
        "CHAT_MODEL_NAME"
    )
    search_platform = os.getenv("SEARCH_PLATFORM", "exa")

    tools = await load_researcher_tools(search_platform=search_platform)
    tools.append(write_research_notes)

    search_agent = create_agent(model_name, tools=tools, system_prompt=SEARCHER_PROMPT)

    await search_agent.ainvoke({"messages": [("human", task)]})

    return


def synthesizer(state: AgentState, runtime: Runtime[AgentContext]):
    """Synthesis and generate the final response"""
    thread_id = runtime.execution_info.thread_id
    run_id = runtime.context.run_id
    fs = get_fs()

    research_node_path = f"{thread_id}/research_note_{run_id}.txt"

    research_notes = None

    if fs.exists(research_node_path):
        research_notes = fs.readtext(research_node_path)

    context = runtime.context
    reason_model_name = getattr(context, "reason_model_name", None) or os.getenv(
        "REASON_MODEL_NAME"
    )

    llm = init_chat_model(reason_model_name)

    prompt = ChatPromptTemplate(
        [
            ("system", SYNTHESIS_PROMPT),
            ("placeholder", "{messages}"),
        ]
    )

    chain = prompt | llm

    response = chain.invoke(
        {"messages": state["messages"], "research_note": research_notes}
    )

    return {"messages": response}
