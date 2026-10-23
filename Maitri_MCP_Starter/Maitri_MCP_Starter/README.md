# Maitri MCP Starter

A minimal local MCP server for the Maitri voice-assistant project. It exposes three tools over Streamable HTTP:

- `get_current_time`
- `add_study_task`
- `list_study_tasks`

The server is bound to `127.0.0.1` for local development. Study tasks are held in memory and disappear when the server stops.

## Requirements

- Standard Windows Python 3.11 or newer (recommended; avoid MSYS2 Python for this project)
- Internet for the initial package installation
- Node.js only if you want to run MCP Inspector with `npx`

## Windows setup (PowerShell)

Open PowerShell in this folder and run:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python server.py
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python server.py
```

The MCP endpoint is:

`http://127.0.0.1:8000/mcp`

Keep the server terminal open while testing.

## Test with MCP Inspector (optional)

Install Node.js LTS from https://nodejs.org/en/download/ and open a new terminal:

```powershell
npx -y @modelcontextprotocol/inspector
```

In Inspector, choose Streamable HTTP and connect to `http://127.0.0.1:8000/mcp`. List tools and test each tool.

## Notes

- This is the MCP-server milestone only. It does not yet include speech recognition or Ollama integration.
- No paid AI API is used by this server.
- Do not expose the server to the public internet as-is. It has no authentication and is intended for local testing.
- Before a hackathon submission, verify the exact current track rules and MCP specification version required by the event.
