from typing import Annotated

from langchain.tools import InjectedToolCallId, ToolRuntime, tool
from langchain.messages import ToolMessage

from app.core.services.file_system import get_fs
from app.schemas.graph import AgentContext


@tool
def write_research_notes(
    note: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    runtime: ToolRuntime[AgentContext],
):
    """Append a research note to a thread-specific file.

    The note is saved to '{thread_id}/research_note_{run_id}.txt' in the file system,
    preceded by a dashed separator line. Use this to persistently store
    observations, ideas, or collected data during a research workflow.

    Args:
        note: The text content to write.
    """

    thread_id = runtime.execution_info.thread_id
    run_id = runtime.context.run_id

    research_node_path = f"{thread_id}/research_note_{run_id}.txt"
    fs = get_fs()

    content = content = f"------------------\n{note}\n\n"

    fs.makedirs(thread_id, recreate=True)
    fs.appendtext(research_node_path, content)

    return ToolMessage(
        content="Write research note successfull",
        tool_call_id=tool_call_id,
    )
