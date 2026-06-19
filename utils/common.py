from langchain.messages import AIMessage

from tools.todo import Todo


def get_next_todo(items: list[Todo], index: int = 0) -> Todo | None:
    if index >= len(items):
        return None

    item = items[index]
    if item.get("status") != "completed":
        return item

    return get_next_todo(items, index + 1)


def get_text_from_llm_response(response: AIMessage):
    blocks = response.content_blocks

    return "\n".join(block["text"] for block in blocks if block["type"] == "text")
