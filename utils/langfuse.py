from langfuse import get_client
from langfuse.langchain import CallbackHandler

_langfuse = None
_langfuse_handler = None


def get_instance():
    global _langfuse, _langfuse_handler

    if _langfuse_handler is None:
        # Initialize Langfuse client
        _langfuse = get_client()

        # Initialize Langfuse CallbackHandler for Langchain (tracing)
        _langfuse_handler = CallbackHandler()

    return _langfuse_handler
