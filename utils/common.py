from langchain.messages import AIMessage

from tools.todo import Todo


def get_text_from_llm_response(response: AIMessage):
    blocks = response.content_blocks

    return "\n".join(block["text"] for block in blocks if block["type"] == "text")
