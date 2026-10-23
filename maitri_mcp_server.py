"""Maitri MCP starter: local time and study-task tools."""
from datetime import datetime
from pathlib import Path
import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Maitri Local Tools")
DATA_DIR = Path.home() / ".maitri"
TASKS_FILE = DATA_DIR / "study_tasks.json"

def load_tasks():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        return []
    try:
        data = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []

def save_tasks(tasks):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TASKS_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")

@mcp.tool()
def get_current_time() -> str:
    """Get the computer's current local date, time, and timezone."""
    now = datetime.now().astimezone()
    return f"Local time: {now.strftime('%A, %d %B %Y, %I:%M:%S %p')} ({now.tzname() or 'local timezone'})."

@mcp.tool()
def add_study_task(title: str, due: str = "") -> str:
    """Add a study task with an optional due-time note."""
    title, due = title.strip(), due.strip()
    if not title:
        return "Task not added: title cannot be empty."
    tasks = load_tasks()
    next_id = max((int(t.get("id", 0)) for t in tasks), default=0) + 1
    task = {"id": next_id, "title": title, "due": due, "completed": False,
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds")}
    tasks.append(task)
    save_tasks(tasks)
    return f"Added study task #{next_id}: {title}" + (f". Due: {due}." if due else ".")

@mcp.tool()
def list_study_tasks(include_completed: bool = False) -> str:
    """List saved study tasks; optionally include completed tasks."""
    tasks = load_tasks()
    if not include_completed:
        tasks = [t for t in tasks if not t.get("completed", False)]
    if not tasks:
        return "No study tasks found."
    return "\n".join(
        f"#{t['id']} [{'done' if t.get('completed') else 'open'}] {t['title']}"
        + (f" | due: {t['due']}" if t.get("due") else "")
        for t in tasks
    )

@mcp.tool()
def complete_study_task(task_id: int) -> str:
    """Mark a task complete by numeric ID."""
    tasks = load_tasks()
    for task in tasks:
        if int(task.get("id", -1)) == int(task_id):
            if task.get("completed"):
                return f"Task #{task_id} is already complete."
            task["completed"] = True
            task["completed_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
            save_tasks(tasks)
            return f"Marked task #{task_id} complete: {task['title']}."
    return f"No task found with ID #{task_id}."

if __name__ == "__main__":
    mcp.run(transport="stdio")
