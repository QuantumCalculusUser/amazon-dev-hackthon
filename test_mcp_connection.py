from maitri_mcp_client import list_tools, call_tool

print("Discovered MCP tools:")
for name, description in list_tools():
    print(f"- {name}: {description}")

print()
print("Testing current time:")
print(call_tool("get_current_time"))

print()
print("Testing study task storage:")
print(call_tool("add_study_task", {"title": "MCP integration test", "due": "delete manually from ~/.maitri/study_tasks.json if desired"}))
print()
print(call_tool("list_study_tasks"))
