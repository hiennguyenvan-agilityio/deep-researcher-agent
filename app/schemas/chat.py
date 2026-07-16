from typing import Literal, NotRequired, TypedDict


class ChatRequest(TypedDict):
    q: NotRequired[str]
    action: NotRequired[Literal["approve", "cancel"]]
    chat_session_id: NotRequired[str]
