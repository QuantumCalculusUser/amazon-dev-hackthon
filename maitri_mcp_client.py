"""
Maitri MCP client helper.

This module launches the separate local Maitri MCP server in its own virtual
environment and provides small synchronous wrappers for the app to call.
It is deliberately isolated from app.py so the current app remains untouched
until the user is ready to integrate and test.
"""
import asyncio
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _server_path():
    # Expected layout:
    # Maitri project/
    #   app.py
    #   indus-pocket-tts/
    #   Maitri_MCP_Starter/maitri_mcp_server.py
    #   Maitri_MCP_Starter/.venv/Scripts/python.exe
    app_dir = Path(__file__).resolve().parent
    candidates = [
        app_dir / "Maitri_MCP_Starter" / "maitri_mcp_server.py",
        app_dir / "Maitri_MCP_Starter_Package" / "Maitri_MCP_Starter" / "maitri_mcp_server.py",
        app_dir / "maitri_mcp_server.py",
    ]
    for server in candidates:
        if server.is_file():
            env_python = server.parent / ".venv" / "Scripts" / "python.exe"
            return server, (env_python if env_python.is_file() else None)
    raise FileNotFoundError(
        "Maitri MCP server not found. Place the MCP starter folder beside app.py "
        "or update the path in maitri_mcp_client.py."
    )


async def _call_tool_async(name, arguments):
    server, env_python = _server_path()
    command = str(env_python) if env_python else "python"
    params = StdioServerParameters(
        command=command,
        args=[str(server)],
        cwd=str(server.parent),
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            pieces = []
            for item in getattr(result, "content", []):
                if getattr(item, "text", None):
                    pieces.append(item.text)
            if getattr(result, "isError", False):
                raise RuntimeError("\\n".join(pieces) or f"MCP tool {name} failed")
            return "\\n".join(pieces) or "(No text returned by tool.)"


def call_tool(name, arguments=None):
    """Call one tool from a normal synchronous Python thread."""
    return asyncio.run(_call_tool_async(name, arguments or {}))


def list_tools():
    async def _list():
        server, env_python = _server_path()
        command = str(env_python) if env_python else "python"
        params = StdioServerParameters(
            command=command,
            args=[str(server)],
            cwd=str(server.parent),
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                return [(tool.name, tool.description or "") for tool in result.tools]
    return asyncio.run(_list())
