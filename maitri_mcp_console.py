"""
Maitri MCP Tools — simple runnable test program
===============================================

Save this file in the SAME folder as maitri_mcp_server.py.
Run it using the .venv created in that folder:

    .venv\Scripts\python.exe maitri_mcp_console.py

This is a standalone console program. It does not modify app.py.
"""

import asyncio
import sys
from pathlib import Path

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("MCP SDK is not installed in this Python environment.")
    print("Run this program with: .venv\\Scripts\\python.exe maitri_mcp_console.py")
    input("Press Enter to close...")
    raise SystemExit(1)


HERE = Path(__file__).resolve().parent
SERVER = HERE / "maitri_mcp_server.py"


async def run_tool(tool_name, arguments=None):
    if not SERVER.is_file():
        raise FileNotFoundError(
            f"Can't find {SERVER.name} beside this program.\n"
            "Put maitri_mcp_console.py in the same folder as maitri_mcp_server.py."
        )

    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
        cwd=str(HERE),
    )

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments or {})
            text_parts = [
                item.text for item in getattr(result, "content", [])
                if getattr(item, "text", None)
            ]
            if getattr(result, "isError", False):
                raise RuntimeError("\n".join(text_parts) or "The MCP tool returned an error.")
            return "\n".join(text_parts) or "(No text returned.)"


async def show_tools():
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
        cwd=str(HERE),
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()
            return [(tool.name, tool.description or "") for tool in result.tools]


def ask(prompt):
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def main():
    print("=" * 48)
    print("       MAITRI MCP TOOLS — TEST CONSOLE")
    print("=" * 48)
    print("This tests your local MCP tools; it does not change app.py.")
    print(f"Server: {SERVER}")
    print()

    if not SERVER.is_file():
        print("ERROR: maitri_mcp_server.py was not found.")
        print("Move this program into the same folder as maitri_mcp_server.py.")
        input("Press Enter to close...")
        return

    try:
        tools = asyncio.run(show_tools())
        print("MCP connection successful. Tools found:")
        for name, description in tools:
            print(f"  - {name}: {description}")
    except Exception as exc:
        print(f"Could not connect to the MCP server: {exc}")
        print("\nCheck that the MCP SDK is installed in this .venv.")
        input("Press Enter to close...")
        return

    while True:
        print("\nChoose an action:")
        print("  1. Check current time")
        print("  2. Add a study task")
        print("  3. List study tasks")
        print("  4. Mark a task complete")
        print("  5. Exit")
        choice = ask("Enter 1-5: ")

        try:
            if choice == "1":
                print("\n" + asyncio.run(run_tool("get_current_time")))
            elif choice == "2":
                title = ask("Task title: ")
                if not title:
                    print("Task title cannot be empty.")
                    continue
                due = ask("Due-time note (optional, e.g. tomorrow at 6 PM): ")
                print("\n" + asyncio.run(run_tool(
                    "add_study_task", {"title": title, "due": due}
                )))
            elif choice == "3":
                include = ask("Include completed tasks? (y/N): ").lower() == "y"
                print("\n" + asyncio.run(run_tool(
                    "list_study_tasks", {"include_completed": include}
                )))
            elif choice == "4":
                raw_id = ask("Task ID to mark complete: ")
                try:
                    task_id = int(raw_id)
                except ValueError:
                    print("Please enter a numeric task ID.")
                    continue
                print("\n" + asyncio.run(run_tool(
                    "complete_study_task", {"task_id": task_id}
                )))
            elif choice == "5":
                print("Maitri MCP test finished.")
                break
            else:
                print("Please choose a number from 1 to 5.")
        except Exception as exc:
            print(f"\nAction failed: {exc}")

    input("\nPress Enter to close...")


if __name__ == "__main__":
    main()
