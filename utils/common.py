from tools.todo import Todo


def get_next_todo(items: list[Todo], index: int = 0) -> Todo | None:
    if index >= len(items):
        return None
    
    item = items[index]
    if item.get("status") != "completed":
        return item

    return get_next_todo(items, index + 1)
