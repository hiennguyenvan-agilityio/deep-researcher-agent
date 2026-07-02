import os
import uuid

from fastapi import (
    APIRouter,
)
from fastapi.responses import StreamingResponse

from app.core.langgraph.graph import get_graph
from app.core.services.langfuse import get_instance
from app.schemas.chat import ChatRequest
from langgraph.checkpoint.memory import MemorySaver


router = APIRouter()

chat_model_name = os.getenv(
    "CHAT_MODEL_NAME", "google_genai:gemini-3.1-flash-lite-preview"
)
reason_model_name = os.getenv(
    "REASON_MODEL_NAME", "google_genai:gemini-3.1-flash-lite-preview"
)

checkpointer = MemorySaver()

chatbot_agent = get_graph(
    chat_model_name=chat_model_name,
    reason_model_name=reason_model_name,
    checkpointer=checkpointer,
)

langfuse_handler = get_instance()


async def stream_from_agent(query: str, chat_session_id: str):
    config = {
        "callbacks": [langfuse_handler],
        "configurable": {"thread_id": chat_session_id},
    }

    async for event in chatbot_agent.astream(
        {"messages": [{"role": "user", "content": query}]},
        stream_mode="messages",
        version="v2",
        config=config,
        subgraphs=True,
    ):
        message, metadata = event["data"]

        if metadata["langgraph_node"] != "synthesizer":
            continue

        yield message.content


@router.post("/chat")
async def chat(chat_request: ChatRequest):
    q = chat_request.get("q")
    chat_session_id = chat_request.get("chat_session_id")

    if q is None:
        return {"error": "No query provided"}

    chat_session_id = chat_session_id or str(uuid.uuid4())
    config = {
        "callbacks": [langfuse_handler],
        "configurable": {"thread_id": chat_session_id},
    }

    response = chatbot_agent.invoke(
        {"messages": [{"role": "user", "content": q}]}, config=config
    )

    return {"messages": response["messages"], "thread_id": chat_session_id}


@router.post("/chat/stream")
async def chat_stream(chat_request: ChatRequest):
    q = chat_request.get("q")
    chat_session_id = chat_request.get("chat_session_id")

    if q is None:
        return {"error": "No query provided"}

    chat_session_id = chat_session_id or str(uuid.uuid4())

    return StreamingResponse(
        stream_from_agent(q, chat_session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Chat-Session-Id": chat_session_id,
        },
    )
