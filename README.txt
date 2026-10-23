MAITRI MCP INTEGRATION — SAFE NEXT STEP
========================================

Your uploaded app.py has been reviewed. It uses Tkinter, calls Ollama directly,
and already has working voice input and spoken replies. This package does not
overwrite or modify that app.py.

FILES
-----
- maitri_mcp_client.py: client helper for connecting to the MCP server over stdio
- test_mcp_connection.py: test that discovers tools and calls them

EXPECTED LAYOUT
---------------
Keep your current app.py and voice folders untouched. Place the client helper
and test script in your project folder (the same folder as app.py).

Your MCP server folder must be available in one of these locations:
1. app folder\\Maitri_MCP_Starter\\maitri_mcp_server.py
2. app folder\\Maitri_MCP_Starter_Package\\Maitri_MCP_Starter\\maitri_mcp_server.py
3. app folder\\maitri_mcp_server.py

The helper looks for a local .venv\\Scripts\\python.exe beside the server.
If the MCP server folder currently lives only in Downloads, either keep it there
and update the path in the helper, or copy the MCP starter folder into the app
folder. Copying is safer than moving your only copy.

TEST
----
Use the same MCP environment you installed the SDK into:
1. Copy these two .py files beside app.py.
2. Open CMD in the MCP starter folder and activate its environment:
   .venv\\Scripts\\activate
3. Run the test script with the full path to it, for example:
   python "C:\\path\\to\\Maitri\\test_mcp_connection.py"

The first call should list the four tools and show the local time.
The task test creates a task named "MCP integration test" in:
%USERPROFILE%\\.maitri\\study_tasks.json
You can delete that test task from the JSON file if you do not want it.

IMPORTANT
---------
This tests MCP transport and tool execution. It does not yet make the chat model
automatically choose tools from natural-language requests. That requires the
next app integration change. Do not replace app.py until this test succeeds.
