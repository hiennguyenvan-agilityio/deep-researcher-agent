import json

from resources.vitual_file_system import get_vfs
from tools.todo import Todo


def completed_task(
    todo: Todo,
    thread_id: str,
):
    """Update task to completed"""
    old_todo = json.dumps(todo)
    updated_todo = json.dumps({**todo, "status": "completed"})

    path = f"todos_{thread_id}.json"
    vfs = get_vfs()

    content = vfs.readtext(path)
    new_content = content.replace(old_todo, updated_todo)

    vfs.writetext(path, new_content)

    return
