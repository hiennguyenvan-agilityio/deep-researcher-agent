from typing import NotRequired, TypedDict


class ChatRequest(TypedDict):
    q: NotRequired[str]
    resume: NotRequired[str]
    chat_session_id: NotRequired[str]
