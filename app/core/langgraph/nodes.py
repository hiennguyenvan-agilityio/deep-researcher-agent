import json
import os
import uuid

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END
from langgraph.types import Command, interrupt
from langgraph.runtime import Runtime
from copilotkit.langgraph import copilotkit_customize_config
from langchain_core.callbacks.manager import adispatch_custom_event

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
    SearchWorkerState,
    SearcherOutput,
    SearcherState,
)
from app.core.constants.graph import initial_state
from app.schemas.todo import Todo


async def initial(_: AgentState):
    # Automatic set execution_id each invoke run
    execution_id = str(uuid.uuid4())

    return {
        # Reset state during each invoke, except resume
        **initial_state,
        "execution_id": execution_id,
    }


async def gatekeeper(state: AgentState, runtime: Runtime[AgentContext]):
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

    modifiedConfig = copilotkit_customize_config(
        emit_messages=False,
    )

    chain = prompt | llm
    response = await chain.ainvoke(state, config=modifiedConfig)

    action = response.action

    if action == "proceed":
        query = response.query

        return {
            "query": query,
            "action": action,
        }

    message = response.message

    return {"messages": AIMessage(content=message), "action": action}


async def orchestrator(state: AgentState, runtime: Runtime[AgentContext]):
    """Orchestrator that generates a plan for the researcher"""

    context = runtime.context
    model_name = getattr(context, "reason_model_name", None) or os.getenv(
        "REASON_MODEL_NAME"
    )
    loop_count = state.get("loop_count", 0) + 1

    if loop_count > int(os.getenv("LOOP_LIMIT", 5)):
        # Workaround for a CopilotKit issue: `TEXT_MESSAGE_CONTENT` events
        # cannot be sent unless a `TEXT_MESSAGE_START` event is sent first.
        # This is a temporary hack; the root cause is still unknown.
        modifiedConfig = copilotkit_customize_config(
            emit_messages=False,
            emit_tool_calls=False,
        )
        llm = init_chat_model(model=model_name)

        response = llm.invoke("hello", config=modifiedConfig)

        return {"orchestrator_messages": [AIMessage(content="Make synthesis")]}

    tools = [write_todos]

    llm = init_chat_model(model=model_name, temperature=0).bind_tools(tools)

    thread_id = runtime.execution_info.thread_id
    execution_id = state["execution_id"]
    fs = get_fs()

    research_node_path = f"{thread_id}/research_note_{execution_id}.txt"

    research_notes = None

    if fs.exists(research_node_path):
        research_notes = fs.readtext(research_node_path)

    prompt = ChatPromptTemplate(
        [
            ("system", ORCHESTRATOR_PROMPT),
            ("human", "{query}"),
        ]
    )

    modifiedConfig = copilotkit_customize_config(
        emit_messages=False, emit_tool_calls=False
    )

    chain = prompt | llm
    response = await chain.ainvoke(
        {
            "query": state["query"],
            "research_notes": research_notes,
        },
        config=modifiedConfig,
    )

    return {"orchestrator_messages": [response], "loop_count": loop_count}


async def searcher(state: SearchWorkerState, runtime: Runtime[AgentContext]):
    """Execute a single search task."""
    task = state["task"]
    execution_id = state["execution_id"]

    context = runtime.context
    model_name = getattr(context, "reason_model_name", None) or os.getenv(
        "CHAT_MODEL_NAME"
    )
    search_platform = os.getenv("SEARCH_PLATFORM", "exa")

    tools = await load_researcher_tools(search_platform=search_platform)
    tools.append(write_research_notes)

    search_agent = create_agent(
        model_name,
        tools=tools,
        system_prompt=SEARCHER_PROMPT,
        state_schema=SearcherState,
        response_format=SearcherOutput,
    )

    modifiedConfig = copilotkit_customize_config(
        emit_messages=False, emit_tool_calls=False
    )

    response = await search_agent.ainvoke(
        {"messages": [("human", task)], "execution_id": execution_id},
        config=modifiedConfig,
    )

    result = json.loads(response["messages"][-1].content)

    status = result["status"]

    if status == "completed":
        # `copilotkit_emit_message` uses an incorrect event name, causing it to fail.
        # Manually dispatch the custom event as a workaround.
        await adispatch_custom_event(
            "manually_emit_message",
            {"message": task, "message_id": str(uuid.uuid4()), "role": "activity"},
        )

    return {"todos": [Todo(content=task, status=status)]}


async def synthesizer(state: AgentState, runtime: Runtime[AgentContext]):
    """Synthesis and generate the final response"""
    thread_id = runtime.execution_info.thread_id
    execution_id = state["execution_id"]
    fs = get_fs()

    research_node_path = f"{thread_id}/research_note_{execution_id}.txt"

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


async def feedback(_: AgentState):
    feedback = interrupt(
        {
            "message": (
                "Are you satisfied with that?\n"
                "\n"
                "If not, tell me what you'd like to improve or what additional research you'd like me to perform."
            ),
            "type": "feedback",
        }
    )

    if feedback:
        return Command(
            goto="gatekeeper",
            update={"messages": HumanMessage(feedback), "loop_count": 0},
        )

    return Command(goto=END)
