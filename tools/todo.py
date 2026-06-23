from typing import Any, Literal, TypedDict
import json

from langchain.tools import ToolRuntime, tool
from langgraph.types import Command

from resources.vitual_file_system import get_vfs

WRITE_TODOS_TOOL_DESCRIPTION = """Use this tool to create and manage a structured task list for your current work session. This helps you track progress and organize complex tasks.

## How to Use This Tool

1. When you start working on a task - Mark it as in_progress BEFORE beginning work.
2. After completing a task - Mark it as completed and add any new follow-up tasks discovered during implementation.
3. You can also update future tasks, such as deleting them if they are no longer necessary, or adding new tasks that are necessary. Don't change previously completed tasks.
4. You can make several updates to the todo list at once. For example, when you complete a task, you can mark the next task you need to start as in_progress.

## Task States and Management

1. **Task States**: Use these states to track progress:
    - pending: Task not yet started
    - in_progress: Currently working on (you can have multiple tasks in_progress at a time if they are not related to each other and can be run in parallel)
    - completed: Task finished successfully

2. **Task Management**:
    - Update task status in real-time as you work
    - Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
    - Complete current tasks before starting new ones
    - Remove tasks that are no longer relevant from the list entirely
    - IMPORTANT: When you write this todo list, you should mark your first task (or tasks) as in_progress immediately!.
    - IMPORTANT: Unless all tasks are completed, you should always have at least one task in_progress.

3. **Task Completion Requirements**:
    - ONLY mark a task as completed when you have FULLY accomplished it
    - If you encounter errors, blockers, or cannot finish, keep the task as in_progress
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

    status: Literal["pending", "in_progress", "completed"]
    """The current status of the todo item."""


@tool(description=WRITE_TODOS_TOOL_DESCRIPTION)
def write_todos(
    todos: list[Todo],
    runtime: ToolRuntime,
) -> Command[Any]:
    """Create and manage a structured task list for your current work session."""
    serialized = json.dumps(todos)
    thread_id = runtime.execution_info.thread_id
    vfs = get_vfs()

    vfs.writetext(f"todos_{thread_id}.json", serialized)

    return

@tool
def completed_task(
    todo: Todo,
    runtime: ToolRuntime,
) -> Command[Any]:
    """Update task to completed"""
    old_todo = json.dumps(todo)
    updated_todo = json.dumps({**todo, "status": "completed"})

    thread_id = runtime.execution_info.thread_id
    path = f"todos_{thread_id}.json"
    vfs = get_vfs()
    
    content = vfs.readtext(path)
    new_content = content.replace(old_todo, updated_todo)
    
    vfs.writetext(path, new_content)

    return
