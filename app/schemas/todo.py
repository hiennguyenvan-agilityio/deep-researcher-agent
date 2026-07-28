from typing import Literal, TypedDict


class Todo(TypedDict):
    """A single search task."""

    content: str
    """The content/description of the todo item."""

    status: Literal["pending", "failed", "completed"]
    """The current status of the todo item."""
