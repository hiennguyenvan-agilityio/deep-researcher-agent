import json
import os
import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)
from fastapi.responses import StreamingResponse
from langgraph.types import Command

from app.core.services.langfuse import get_instance
from app.schemas.chat import ChatRequest

from langgraph.graph.state import CompiledStateGraph

router = APIRouter()

langfuse_handler = get_instance()

DB_URI = (
    f"postgresql://"
    f"{os.getenv('CHECKPOINTER_DB_USER')}:"
    f"{os.getenv('CHECKPOINTER_DB_PASSWORD')}@"
    f"{os.getenv('CHECKPOINTER_DB_HOST')}:"
    f"{os.getenv('CHECKPOINTER_DB_PORT')}/"
    f"{os.getenv('CHECKPOINTER_DB_NAME')}"
)


async def stream_from_agent(
    graph: CompiledStateGraph,
    query: str | None,
    resume: str | None,
    chat_session_id: str,
):
    config = {
        "callbacks": [langfuse_handler],
        "configurable": {"thread_id": chat_session_id},
    }

    if resume is not None:
        parsed_resume = (
            {"true": True, "false": False}.get(resume.lower(), resume)
            if isinstance(resume, str)
            else resume
        )
        graph_input = Command(resume=parsed_resume)
    else:
        graph_input = {
            "messages": [
                {
                    "role": "user",
                    "content": query,
                }
            ]
        }

    async for event in graph.astream(
        graph_input,
        stream_mode="messages",
        version="v2",
        config=config,
        subgraphs=True,
    ):
        message, metadata = event["data"]

        yield json.dumps(
            {
                "type": event["type"],
                "node": metadata.get("langgraph_node"),
                "content": message.content,
            }
        )


@router.post("/chat")
async def chat(params: ChatRequest, request: Request):
    q = params.get("q")
    resume = params.get("resume")
    chat_session_id = params.get("chat_session_id")

    # Either q or action must be provided
    if q is None and resume is None:
        raise HTTPException(
            status_code=400,
            detail="Either 'q' or 'action' must be provided.",
        )

    # If action is provided, chat_session_id is required
    if resume is not None and chat_session_id is None:
        raise HTTPException(
            status_code=400,
            detail="'chat_session_id' is required when 'action' is provided.",
        )

    chat_session_id = chat_session_id or str(uuid.uuid4())
    config = {
        "callbacks": [langfuse_handler],
        "configurable": {"thread_id": chat_session_id},
    }

    chatbot_agent = request.app.state.graph

    if resume is not None:
        parsed_resume = (
            {"true": True, "false": False}.get(resume.lower(), resume)
            if isinstance(resume, str)
            else resume
        )

        # Resume from an interrupt
        response = await chatbot_agent.ainvoke(
            Command(resume=parsed_resume),
            config=config,
        )
    else:
        # Start a new conversation
        response = await chatbot_agent.ainvoke(
            {"messages": [{"role": "user", "content": q}]},
            config=config,
        )

    return {"messages": response["messages"], "thread_id": chat_session_id}


@router.post("/chat/stream")
async def chat_stream(params: ChatRequest, request: Request):
    q = params.get("q")
    resume = params.get("resume")
    chat_session_id = params.get("chat_session_id")

    # Either q or action must be provided
    if q is None and resume is None:
        raise HTTPException(
            status_code=400,
            detail="Either 'q' or 'action' must be provided.",
        )

    # If action is provided, chat_session_id is required
    if resume is not None and chat_session_id is None:
        raise HTTPException(
            status_code=400,
            detail="'chat_session_id' is required when 'action' is provided.",
        )

    chat_session_id = chat_session_id or str(uuid.uuid4())
    graph = request.app.state.graph

    return StreamingResponse(
        stream_from_agent(
            graph=graph, query=q, resume=resume, chat_session_id=chat_session_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Chat-Session-Id": chat_session_id,
        },
    )
