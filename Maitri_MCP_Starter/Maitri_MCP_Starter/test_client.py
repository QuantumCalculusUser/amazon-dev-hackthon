"""Optional Python MCP client for testing the local server without Node.js."""
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    async with streamablehttp_client("http://127.0.0.1:8000/mcp") as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            result = await session.call_tool("get_current_time", {})
            print("\nTime tool result:")
            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)

            result = await session.call_tool(
                "add_study_task", {"task": "Revise calculus"}
            )
            print("\nAdd task result:")
            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)

            result = await session.call_tool("list_study_tasks", {})
            print("\nTask list result:")
            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)


if __name__ == "__main__":
    asyncio.run(main())
