from typing import TypeVar

from app.schemas.todo import Todo


def merge_todos(current: list[Todo], updates: list[Todo]) -> list[Todo]:
    todos = {todo["content"]: todo for todo in current}

    for update in updates:
        todos[update["content"]] = update

    return list(todos.values())


T = TypeVar("T")


def replace_at_indices(
    items: list[T],
    replacements: dict[int, T] | None = None,
) -> list[T]:
    if not replacements:
        return items

    return [replacements.get(index, item) for index, item in enumerate(items)]
