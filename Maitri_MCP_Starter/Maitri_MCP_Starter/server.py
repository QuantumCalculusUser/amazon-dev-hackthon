from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Local-only MCP server using Streamable HTTP.
# Keep it bound to 127.0.0.1 for local development.
mcp = FastMCP(
    "Maitri",
    host="127.0.0.1",
    port=8000,
    stateless_http=True,
)

study_tasks: list[str] = []


@mcp.tool()
def get_current_time() -> str:
    """Get the computer's current local date and time."""
    return datetime.now().astimezone().strftime(
        "%A, %d %B %Y, %I:%M:%S %p %Z"
    )


@mcp.tool()
def add_study_task(task: str) -> str:
    """Add a study task to Maitri's in-memory task list."""
    task = task.strip()
    if not task:
        return "Please provide a task."
    if len(task) > 200:
        return "Task is too long. Keep it under 200 characters."
    study_tasks.append(task)
    return f"Added task #{len(study_tasks)}: {task}"


@mcp.tool()
def list_study_tasks() -> list[str]:
    """List study tasks added during this server session."""
    return study_tasks.copy()


if __name__ == "__main__":
    # MCP Streamable HTTP endpoint: http://127.0.0.1:8000/mcp
    mcp.run(transport="streamable-http")
