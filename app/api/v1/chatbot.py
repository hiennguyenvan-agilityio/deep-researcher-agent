import uuid

from fastapi import (
    APIRouter,
)
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest

router = APIRouter()


async def stream_from_agent(query: str, chat_session_id: str):
    print("query", query)
    print("chat_session_id", chat_session_id)
    yield "chat_stream"


@router.post("/chat/stream")
async def chat_stream(chat_request: ChatRequest):
    q = chat_request["q"]
    chat_session_id = chat_request["chat_session_id"]

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
