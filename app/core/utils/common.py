from app.schemas.todo import Todo


def merge_todos(current: list[Todo], updates: list[Todo]) -> list[Todo]:
    todos = {todo["content"]: todo for todo in current}

    for update in updates:
        todos[update["content"]] = update

    return list(todos.values())
