from typing import Annotated

from fastmcp import FastMCP
from langchain.messages import ToolMessage
from langchain.tools import InjectedToolCallId
from langgraph.types import Command

from app.schemas.todo import Todo

todo_mcp = FastMCP("todo")


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


@todo_mcp.tool(description=WRITE_TODOS_TOOL_DESCRIPTION, tags={"planner"})
def write_todos(
    todos: list[Todo],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Create and manage a structured task list for your current work session."""

    return Command(
        update={
            "todos": todos,
            "messages": [
                ToolMessage(
                    content="Write todo call success.",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )
