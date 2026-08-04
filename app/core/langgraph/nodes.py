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
from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_core.runnables import RunnableConfig

from llm_guard import scan_prompt
from llm_guard.input_scanners import (
    PromptInjection,
    TokenLimit,
    Toxicity,
    InvisibleText,
)

from app.core.langgraph.tools.mcp import load_researcher_tools
from app.core.langgraph.tools.research_note import write_research_notes
from app.core.langgraph.tools.todo import write_todos
from app.core.prompts import (
    ORCHESTRATOR_PROMPT,
    REFUSE_PROMPT,
    REQUEST_TOO_LONG_SUB_PROMPT,
    SEARCHER_PROMPT,
    SYNTHESIS_PROMPT,
)
from app.core.services.aws import apply_guardrail
from app.core.services.file_system import get_fs
from app.core.services.opa import get_opa_data
from app.core.utils.common import replace_at_indices
from app.core.utils.llm import get_last_message_content
from app.core.utils.nodes import get_node_config
from app.schemas.graph import (
    AgentContext,
    AgentState,
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
    token_limit = getattr(context, "token_limit", None) or os.getenv(
        "TOKEN_LIMIT", 4096
    )

    input_scanners = [
        TokenLimit(limit=token_limit),
        PromptInjection(),
        Toxicity(),
        InvisibleText(),
    ]

    last_message = get_last_message_content(state["messages"])
    index = len(state["messages"]) - 1

    reason_model_name = getattr(context, "chat_model_name", None) or os.getenv(
        "CHAT_MODEL_NAME"
    )
    llm = init_chat_model(reason_model_name)

    sanitized_message, results_valid, _ = scan_prompt(input_scanners, last_message)

    should_refuse = not all(
        (
            results_valid["TokenLimit"],
            results_valid["PromptInjection"],
            results_valid["Toxicity"],
        )
    )

    if should_refuse:
        prompt = REFUSE_PROMPT

        if not results_valid["TokenLimit"]:
            prompt += REQUEST_TOO_LONG_SUB_PROMPT

        response = await llm.ainvoke(prompt)

        return Command(
            goto=END,
            update={
                "messages": response,
                "sanitized_messages": {index: HumanMessage(content="")},
            },
        )

    # Guardrail check
    if os.getenv("BEDROCK_GUARDRAIL_ID") and await apply_guardrail(
        last_message, "INPUT"
    ):
        response = await llm.ainvoke(REFUSE_PROMPT)

        return Command(
            goto=END,
            update={
                "messages": response,
                "sanitized_messages": {index: HumanMessage(content="")},
            },
        )

    sanitized_messages = {}

    if sanitized_message != last_message:
        sanitized_messages[index] = HumanMessage(content=sanitized_message)

    return Command(
        goto="orchestrator",
        update={"sanitized_messages": sanitized_messages},
    )


async def orchestrator(
    state: AgentState, config: RunnableConfig, runtime: Runtime[AgentContext]
):
    """Orchestrator that generates a plan for the researcher"""

    context = runtime.context
    model_name = getattr(context, "reason_model_name", None) or os.getenv(
        "REASON_MODEL_NAME"
    )
    loop_count = state.get("loop_count", 0) + 1

    if loop_count > int(os.getenv("LOOP_LIMIT", 5)):
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
            ("placeholder", "{messages}"),
        ]
    )

    messages = replace_at_indices(state["messages"], state.get("sanitized_messages"))

    modifiedConfig = get_node_config(config, emit_messages=False, emit_tool_calls=False)

    chain = prompt | llm
    response = await chain.ainvoke(
        {
            "messages": messages,
            "research_notes": research_notes,
        },
        config=modifiedConfig,
    )

    return {"orchestrator_messages": [response], "loop_count": loop_count}


async def searcher(
    state: SearchWorkerState, config: RunnableConfig, runtime: Runtime[AgentContext]
):
    """Execute a single search task."""
    task = state["task"]
    execution_id = state["execution_id"]

    context = runtime.context
    model_name = getattr(context, "chat_model_name", None) or os.getenv(
        "CHAT_MODEL_NAME"
    )
    user = context.user
    opa_input = {
        "user": {
            "id": user.id,
            "email": user.email,
        }
        if user
        else None
    }

    data = await get_opa_data(
        "deep_researcher/search_platform",
        opa_input,
        default={"search_platform": "duckduckgo"},
    )

    tools = await load_researcher_tools(search_platform=data.get("search_platform"))
    tools.append(write_research_notes)

    search_agent = create_agent(
        model_name,
        tools=tools,
        system_prompt=SEARCHER_PROMPT,
        state_schema=SearcherState,
        response_format=SearcherOutput,
    )

    modifiedConfig = get_node_config(config, emit_messages=False, emit_tool_calls=False)

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


async def synthesizer(
    state: AgentState, config: RunnableConfig, runtime: Runtime[AgentContext]
):
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

    modifiedConfig = get_node_config(config, emit_messages=True, emit_tool_calls=False)

    chain = prompt | llm

    response = await chain.ainvoke(
        {"messages": state["messages"], "research_note": research_notes},
        config=modifiedConfig,
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
