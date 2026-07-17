import json
import os
from typing import Literal
import uuid

from fastapi import (
    APIRouter,
    HTTPException,
)
from fastapi.responses import StreamingResponse
from langgraph.types import Command

from app.core.langgraph.graph import get_graph
from app.core.services.langfuse import get_instance
from app.schemas.chat import ChatRequest

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

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
    query: str | None,
    action: Literal["approve", "reject"] | None,
    chat_session_id: str,
):
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        config = {
            "callbacks": [langfuse_handler],
            "configurable": {"thread_id": chat_session_id},
        }

        chatbot_agent = await get_graph(checkpointer=checkpointer)

        if action is not None:
            graph_input = Command(resume=(action == "approve"))
        else:
            graph_input = {
                "messages": [
                    {
                        "role": "user",
                        "content": query,
                    }
                ]
            }

        async for event in chatbot_agent.astream(
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
async def chat(chat_request: ChatRequest):
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        q = chat_request.get("q")
        action = chat_request.get("action")
        chat_session_id = chat_request.get("chat_session_id")

        # Either q or action must be provided
        if q is None and action is None:
            raise HTTPException(
                status_code=400,
                detail="Either 'q' or 'action' must be provided.",
            )

        # If action is provided, chat_session_id is required
        if action is not None and chat_session_id is None:
            raise HTTPException(
                status_code=400,
                detail="'chat_session_id' is required when 'action' is provided.",
            )

        chat_session_id = chat_session_id or str(uuid.uuid4())
        config = {
            "callbacks": [langfuse_handler],
            "configurable": {"thread_id": chat_session_id},
        }

        chatbot_agent = await get_graph(checkpointer=checkpointer)

        if action is not None:
            # Resume from an interrupt
            response = await chatbot_agent.ainvoke(
                Command(resume=(action == "approve")),
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
async def chat_stream(chat_request: ChatRequest):
    q = chat_request.get("q")
    action = chat_request.get("action")
    chat_session_id = chat_request.get("chat_session_id")

    # Either q or action must be provided
    if q is None and action is None:
        raise HTTPException(
            status_code=400,
            detail="Either 'q' or 'action' must be provided.",
        )

    # If action is provided, chat_session_id is required
    if action is not None and chat_session_id is None:
        raise HTTPException(
            status_code=400,
            detail="'chat_session_id' is required when 'action' is provided.",
        )

    chat_session_id = chat_session_id or str(uuid.uuid4())

    return StreamingResponse(
        stream_from_agent(query=q, action=action, chat_session_id=chat_session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Chat-Session-Id": chat_session_id,
        },
    )
