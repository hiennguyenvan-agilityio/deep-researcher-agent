from typing import Literal, TypedDict


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
