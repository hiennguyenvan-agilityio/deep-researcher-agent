from langchain.messages import AIMessage, AnyMessage


def get_text_from_llm_response(response: AIMessage):
    blocks = response.content_blocks

    return "\n".join(block["text"] for block in blocks if block["type"] == "text")


def get_last_message_content(messages: list[AnyMessage]) -> str | None:
    if len(messages) == 0:
        return None

    last_message = messages[-1]
    text = (
        last_message.content
        if isinstance(last_message.content, str)
        else str(last_message.content)
    )

    return text
