# Maitri MCP Integration

A safe, non-invasive first step for connecting the **Maitri** desktop assistant to an **MCP (Model Context Protocol) server** over stdio.

Maitri's existing `app.py` is a Tkinter application that calls Ollama directly and already supports voice input and spoken replies. This package **does not overwrite or modify `app.py`**. It only adds a client helper and a test script so you can verify that MCP transport and tool execution work before touching the main app.

---

## Table of Contents

- [Overview](#overview)
- [Files](#files)
- [Expected Project Layout](#expected-project-layout)
- [MCP Server Locations](#mcp-server-locations)
- [Setup](#setup)
- [Running the Test](#running-the-test)
- [Expected Results](#expected-results)
- [Test Data and Cleanup](#test-data-and-cleanup)
- [Important Limitations](#important-limitations)
- [Next Steps](#next-steps)

---

## Overview

| Item | Status |
|------|--------|
| Existing `app.py` (Tkinter + Ollama + voice in/out) | Untouched |
| MCP client helper over stdio | Included |
| Tool discovery and tool-call test | Included |
| Chat model automatically choosing tools from natural language | **Not yet implemented** |

This package tests **MCP transport and tool execution only**.

---

## Files

| File | Purpose |
|------|---------|
| `maitri_mcp_client.py` | Client helper that connects to the MCP server over stdio |
| `test_mcp_connection.py` | Test script that discovers the server's tools and calls them |

---

## Expected Project Layout

Keep your current `app.py` and voice folders as they are. Place the two files above in your project folder, in the same folder as `app.py`.

```text
Maitri/
├── app.py                      # existing app (unchanged)
├── maitri_mcp_client.py        # added
├── test_mcp_connection.py      # added
├── (your existing voice folders)
└── Maitri_MCP_Starter/         # MCP server folder (see locations below)
    ├── maitri_mcp_server.py
    └── .venv/
```

---

## MCP Server Locations

The helper looks for `maitri_mcp_server.py` in one of these locations, relative to the app folder:

1. `Maitri_MCP_Starter\maitri_mcp_server.py`
2. `Maitri_MCP_Starter_Package\Maitri_MCP_Starter\maitri_mcp_server.py`
3. `maitri_mcp_server.py`

The helper also looks for a local virtual environment Python interpreter beside the server:

```text
.venv\Scripts\python.exe
```

If your MCP server folder currently lives only in `Downloads`, you can either:

- keep it there and update the path in `maitri_mcp_client.py`, or
- copy the MCP starter folder into the app folder.

> **Tip:** Copying is safer than moving, especially if it is your only copy.

---

## Setup

1. Copy `maitri_mcp_client.py` and `test_mcp_connection.py` next to `app.py`.
2. Make sure the MCP server folder is in one of the locations listed above.
3. Make sure the MCP Python SDK is installed in the MCP starter folder's virtual environment.

---

## Running the Test

Use the same environment you installed the MCP SDK into.

1. Open **Command Prompt** in the MCP starter folder.
2. Activate its virtual environment:

   ```bat
   .venv\Scripts\activate
   ```

3. Run the test script using its full path, for example:

   ```bat
   python "C:\path\to\Maitri\test_mcp_connection.py"
   ```

---

## Expected Results

- The first call should **list the four available tools** and **show the local time**.
- The task test creates a task named `MCP integration test`.

---

## Test Data and Cleanup

The task test writes to:

```text
%USERPROFILE%\.maitri\study_tasks.json
```

If you do not want to keep the test task, open that JSON file and delete the entry named `MCP integration test`.

---

## Important Limitations

- This test verifies **MCP transport and tool execution** only.
- It does **not** yet make the chat model choose tools automatically from natural-language requests. That requires a further change to the app integration.
- **Do not replace `app.py` until this test succeeds.**

---

## Next Steps

1. Confirm `test_mcp_connection.py` runs cleanly end to end.
2. Integrate the MCP client into `app.py` so the chat model can select and call tools from natural-language requests.
