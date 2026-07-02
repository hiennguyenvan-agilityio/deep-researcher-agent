from typing import Any, Literal, TypedDict
import json

from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command

from app.core.services.file_system import get_fs

WRITE_TODOS_TOOL_DESCRIPTION = """Use this tool to create and manage a structured task list for your current work session. This helps you track progress and organize complex tasks.

## Task States and Management

1. **Task States**: Use these states to track progress:
    - pending: Task not yet started
    - completed: Task finished successfully

2. **Task Management**:
    - Update task status in real-time as you work
    - Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
    - Complete current tasks before starting new ones
    - Remove tasks that are no longer relevant from the list entirely

3. **Task Completion Requirements**:
    - ONLY mark a task as completed when you have FULLY accomplished it
    - When blocked, create a new task describing what needs to be resolved
    - Never mark a task as completed if:
        - There are unresolved issues or errors
        - Work is partial or incomplete
        - You encountered blockers that prevent completion
        - You couldn't find necessary resources or dependencies
        - Quality standards haven't been met

4. **Task Breakdown**:
    - Create specific, actionable items
    - Break complex tasks into smaller, manageable steps
    - Use clear, descriptive task names

Being proactive with task management ensures you complete all requirements successfully
Remember: If you only need to make a few tool calls to complete a task, and it is clear what you need to do, it is better to just do the task directly and NOT call this tool at all.

## When You Finish

`write_todos` tracks your work; it does not deliver the answer. Whatever the user asked for — computations, summaries, comparisons, data — must appear as text content in a message after your final `write_todos` call. Marking the last todo complete is not itself an answer to the user."""


class Todo(TypedDict):
    """A single todo item with content and status."""

    content: str
    """The content/description of the todo item."""

    status: Literal["pending", "completed"]
    """The current status of the todo item."""

    step: int
    (
        "The execution stage of the task.\n"
        "\n"
        "Assign the same step number to tasks that are independent and can be executed\n"
        "in parallel. Only increment the step when a task depends on the completion or\n"
        "results of tasks in earlier steps."
    )


@tool(description=WRITE_TODOS_TOOL_DESCRIPTION)
def write_todos(
    todos: list[Todo],
    runtime: ToolRuntime,
) -> Command[Any]:
    """Create and manage a structured task list for your current work session."""
    serialized = json.dumps(todos)
    thread_id = runtime.execution_info.thread_id
    fs = get_fs()

    fs.writetext(f"todos_{thread_id}.json", serialized)

    return ToolMessage(
        content=f"Successfully saved {len(todos)} todos.",
        tool_call_id=runtime.tool_call_id,
    )
