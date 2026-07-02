from typing import Optional, TypedDict


class ChatRequest(TypedDict):
    q: str
    chat_session_id: Optional[str] = None
