from typing import Annotated

from langchain.tools import InjectedToolCallId, ToolRuntime, tool
from langchain.messages import ToolMessage

from app.core.services.file_system import get_fs
from app.schemas.graph import AgentContext, SearcherState


@tool
def write_research_notes(
    note: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    runtime: ToolRuntime[AgentContext, SearcherState],
):
    """Persist a research finding for the current research execution.

    Use this tool to save relevant findings, observations, or useful information
    discovered during the search task. The note is appended to a
    thread-specific file at:
        {thread_id}/research_note_{execution_id}.txt

    Do not call this tool when the research task produces no relevant or useful information.

    Args:
        note: The research finding or information worth preserving.
    """

    thread_id = runtime.execution_info.thread_id
    execution_id = runtime.state["execution_id"]

    research_node_path = f"{thread_id}/research_note_{execution_id}.txt"
    fs = get_fs()

    content = f"------------------\n{note}\n\n"

    fs.makedirs(thread_id, recreate=True)
    fs.appendtext(research_node_path, content)

    return ToolMessage(
        content="Write research note successfull",
        tool_call_id=tool_call_id,
    )
