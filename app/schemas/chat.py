from typing import NotRequired, TypedDict


class ChatRequest(TypedDict):
    q: str
    chat_session_id: NotRequired[str]
