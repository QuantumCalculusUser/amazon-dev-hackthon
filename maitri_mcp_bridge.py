"""Maitri MCP bridge; supports both flat and nested MCP folder layouts."""
import asyncio
import json
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def main():
    if len(sys.argv) < 2:
        print("Usage: maitri_mcp_bridge.py TOOL_NAME [JSON_ARGUMENTS]", file=sys.stderr)
        return 2
    name = sys.argv[1]
    try:
        arguments = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    except json.JSONDecodeError as exc:
        print(f"Invalid arguments: {exc}", file=sys.stderr)
        return 2

    app_dir = Path(__file__).resolve().parent
    nested = app_dir / "Maitri_MCP_Starter"
    server = nested / "maitri_mcp_server.py"
    if not server.is_file():
        server = app_dir / "maitri_mcp_server.py"
    if not server.is_file():
        print(
            "MCP server not found. Expected maitri_mcp_server.py beside app.py "
            "or inside Maitri_MCP_Starter.",
            file=sys.stderr,
        )
        return 2

    async def call():
        params = StdioServerParameters(
            command=sys.executable,
            args=[str(server)],
            cwd=str(server.parent),
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
                pieces = [
                    item.text for item in getattr(result, "content", [])
                    if getattr(item, "text", None)
                ]
                if getattr(result, "isError", False):
                    raise RuntimeError("\n".join(pieces) or "MCP tool error")
                return "\n".join(pieces) or "(No text returned by MCP tool.)"

    try:
        print(asyncio.run(call()))
        return 0
    except Exception as exc:
        print(f"MCP call failed: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
