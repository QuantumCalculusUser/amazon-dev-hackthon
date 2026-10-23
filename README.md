# Maitri — Complete Setup, Usage, and Troubleshooting Manual

> **Project type:** Offline-first desktop AI assistant for Windows  
> **Interface:** Python/Tkinter desktop window  
> **Local language model:** Ollama with `qwen2.5:7b`  
> **Voice input:** Microphone + `sounddevice` + Vosk speech recognition  
> **Voice output:** Windows SAPI5 / `pyttsx3` for English; local Pocket TTS workflow for Devanagari Hindi  
> **Tool integration:** Local Model Context Protocol (MCP) server over standard input/output (stdio)

This manual describes the Maitri build that includes the desktop chat window, Ollama chat, microphone transcription, spoken replies, and four local MCP tools. Some behaviour depends on the exact files included in the submitted repository. If a file or model is not included, follow the installation instructions below rather than assuming it is already present.

---

## Contents

1. [What Maitri is](#1-what-maitri-is)
2. [Features and current limits](#2-features-and-current-limits)
3. [How the parts work together](#3-how-the-parts-work-together)
4. [Hardware and operating-system requirements](#4-hardware-and-operating-system-requirements)
5. [Software and model checklist](#5-software-and-model-checklist)
6. [Recommended project folder layout](#6-recommended-project-folder-layout)
7. [Install everything from a clean Windows computer](#7-install-everything-from-a-clean-windows-computer)
8. [Start Maitri](#8-start-maitri)
9. [Use the desktop interface](#9-use-the-desktop-interface)
10. [Use voice input and spoken replies](#10-use-voice-input-and-spoken-replies)
11. [Use the MCP tools](#11-use-the-mcp-tools)
12. [Task storage, privacy, and backups](#12-task-storage-privacy-and-backups)
13. [Configuration reference](#13-configuration-reference)
14. [Troubleshooting](#14-troubleshooting)
15. [Testing checklist](#15-testing-checklist)
16. [Security and limitations](#16-security-and-limitations)
17. [Project structure and responsibilities](#17-project-structure-and-responsibilities)
18. [Reproducibility checklist for maintainers](#18-reproducibility-checklist-for-maintainers)

---

## 1. What Maitri is

Maitri is a Windows desktop assistant designed to run a language model locally rather than sending normal chat messages to a hosted AI API. It supports typed conversation, a short microphone recording, speech-to-text, spoken answers, and a small set of local productivity tools exposed through MCP.

Maitri is a Python application, not a cloud service. Ollama runs the language model on the same computer, and the MCP server stores study tasks in a JSON file in the user's home directory.

### Intended use

- Ask questions and have a normal conversation with the local language model.
- Talk to Maitri using a microphone and have the recognized words sent as a message.
- Hear replies spoken aloud.
- Ask for the computer's current local date and time.
- Create and list study tasks.
- Mark a study task complete by its numeric task ID.

### Important distinction

A task with a due phrase such as “tomorrow” is currently saved as **text describing a due time**. The current implementation does **not** schedule a notification or automatically remind the user later. A task list is not a reminder scheduler, despite how naturally humans keep trying to make one into the other.

---

## 2. Features and current limits

| Feature | What it does | Important limits |
|---|---|---|
| Local AI chat | Sends conversation messages to Ollama's local API using `qwen2.5:7b` | The model must be downloaded and Ollama must be running |
| Desktop UI | Displays messages in a Tkinter window | Windows desktop build; not a mobile or web app |
| English voice input | Records up to six seconds, then transcribes with Vosk | The configured model is English (`vosk-model-small-en-us-0.15`); accuracy varies with accent, noise, and microphone quality |
| Voice-triggered chat | Fills the recognized transcript into the message flow and sends it | Speech recognition can mishear names, numbers, and commands; check the displayed transcript |
| Spoken English replies | Uses `pyttsx3` with Windows SAPI5 voices | The voice available depends on Windows speech voices installed on the computer |
| Spoken Hindi replies | If the response contains Devanagari characters, runs the local `indus-pocket-tts/speak.py` workflow and plays the generated WAV | The script, its Python dependencies, model assets, and Python 3.14 installation must all be present |
| Current local time | MCP tool reads the computer's local time and timezone | Depends on the Windows clock and timezone settings |
| Add study task | Saves a task title and optional due-time note | Does not create a scheduled notification |
| List study tasks | Lists open tasks by default; can include completed tasks | Tasks persist in a local JSON file |
| Complete study task | Marks a task complete by numeric ID | The correct task ID must be supplied |
| Natural-language tool selection | Asks the local Qwen model to choose from a fixed list of allowed tools | It is an intent router, not guaranteed perfect; inspect tool results |
| MCP integration | Connects to the local MCP server through a Python bridge | The described build uses MCP stdio transport, not a network-hosted MCP service |

### Not currently implemented by this build

Do not claim these as existing features unless you add and test them separately:

- Automatic timed reminders, notifications, or alarm scheduling.
- Running reminders while Maitri is closed.
- Guaranteed startup after Windows reboots.
- Calendar, email, WhatsApp, browser, smart-home, or Amazon Alexa account integration.
- A web/mobile client or multi-user synchronization.
- Guaranteed perfect speech recognition or factual accuracy.
- Guaranteed fully offline installation. Initial installation, package downloads, and model downloads require internet; normal local inference can run offline after all required assets are installed.
- Automatic deletion of old conversation history from RAM during the current app session. The chat messages are kept in the application's in-memory message list while it runs.

---

## 3. How the parts work together

1. **Tkinter** displays the chat window and controls.
2. **Ollama** serves the `qwen2.5:7b` model through `http://127.0.0.1:11434`.
3. For ordinary chat, Maitri sends the conversation to Ollama's `/api/chat` endpoint.
4. For a possible action, the local model is asked to select from a fixed allowlist of four MCP tools. If that routing step fails, the app also has a small phrase-based fallback for supported commands.
5. **`maitri_mcp_bridge.py`** launches a separate Python process and connects to the MCP server through stdio.
6. **`maitri_mcp_server.py`** performs the selected action and returns text to Maitri.
7. **Vosk** transcribes the microphone recording into text. That text is then handled like a typed message.
8. **Speech output** selects a path based on the reply text: Devanagari Hindi uses the Pocket TTS script; other replies use Windows SAPI5 through `pyttsx3`.

### Local endpoints and files

- Ollama API: `http://127.0.0.1:11434/api/chat`
- Ollama model list: `http://127.0.0.1:11434/api/tags`
- Task data: `%USERPROFILE%\.maitri\study_tasks.json`
- Vosk English model directory: `vosk-model-small-en-us-0.15`
- Hindi speech script expected by the app: `indus-pocket-tts\speak.py`

The Ollama endpoint is loopback-only in the app configuration. Do not change it to a public network address unless you understand the security implications.

---

## 4. Hardware and operating-system requirements

### Required

- Windows 10 or Windows 11, 64-bit.
- A modern CPU and enough RAM to run a 7-billion-parameter model. **16 GB RAM is a practical recommendation**; less may work with reduced performance or memory pressure.
- Several gigabytes of free disk space for Python packages, the Ollama model, speech-recognition model, and Hindi speech assets. The exact amount depends on model quantization and installed dependencies; leave at least 10–15 GB free if possible.
- Microphone for voice input.
- Speakers or headphones for spoken replies.
- Internet connection for initial setup and downloads.
- Permission to install Python packages and run local applications.

### Optional

- A supported GPU may improve local model speed, depending on Ollama's hardware support and drivers. CPU inference is possible but may be slower.
- A webcam is not used by this build.
- A dedicated GPU is not required.

---

## 5. Software and model checklist

Install the following components. Use the official websites rather than third-party “driver download” sites.

| Component | Purpose | Required? |
|---|---|---|
| Python 3.14 (64-bit) | Main app dependencies and the configured Hindi TTS subprocess | Yes for this documented build |
| Python launcher (`py`) | Lets Windows select Python versions with `py -3.14` | Strongly recommended; verify during setup |
| Ollama for Windows | Runs the local language model and exposes its local API | Yes |
| `qwen2.5:7b` Ollama model | Local language generation and tool intent routing | Yes |
| Python packages `sounddevice`, `numpy`, `vosk`, `pyttsx3` | Audio recording, audio data, speech recognition, and English TTS | Yes for the listed features |
| `pywin32` | Provides `pythoncom` for Windows SAPI5 speech in background threads | Recommended if the current Python environment requires it |
| Vosk English model `vosk-model-small-en-us-0.15` | Offline English speech recognition | Yes for the configured microphone feature |
| MCP Python SDK (`mcp`) | Client/server protocol for local tools | Yes for MCP tools |
| `maitri_mcp_bridge.py` and `maitri_mcp_server.py` | Connect app to the MCP tools | Yes for MCP tools |
| `indus-pocket-tts` folder and its dependencies/assets | Local Hindi speech output | Yes for the documented Hindi TTS feature |
| Tkinter | Desktop UI toolkit | Normally included with the official Windows Python installer |

### Official download pages

- Python: https://www.python.org/downloads/windows/
- Ollama: https://ollama.com/download/windows
- Vosk models: https://alphacephei.com/vosk/models
- Vosk documentation: https://alphacephei.com/vosk/
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- `sounddevice`: https://python-sounddevice.readthedocs.io/
- `pyttsx3`: https://pyttsx3.readthedocs.io/

**Hindi TTS note:** The app expects the project to include `indus-pocket-tts\speak.py`, and it explicitly starts that script with `py -3.14`. The exact package requirements and model assets for that folder must be taken from the version of `indus-pocket-tts` bundled with the project. Do not assume the Hindi voice will work from `pyttsx3` alone.

---

## 6. Recommended project folder layout

Keep the application files together. The following layout is supported by the current app and bridge:

```text
Maitri/
├── app.py
├── maitri_mcp_bridge.py
├── maitri_mcp_server.py
├── vosk-model-small-en-us-0.15/
│   └── ... Vosk model files ...
├── indus-pocket-tts/
│   ├── speak.py
│   └── ... TTS code, assets, and required files ...
├── .venv/                         # MCP virtual environment, if using flat layout
│   └── Scripts/
│       └── python.exe
├── requirements.txt               # Recommended to include in the repository
├── README.md
└── START_MAITRI_FIXED.bat         # Optional Windows launcher
```

Alternatively, the MCP files and MCP `.venv` can be inside a `Maitri_MCP_Starter/` subfolder:

```text
Maitri/
├── app.py
├── maitri_mcp_bridge.py
├── vosk-model-small-en-us-0.15/
├── indus-pocket-tts/
└── Maitri_MCP_Starter/
    ├── maitri_mcp_server.py
    └── .venv/
        └── Scripts/
            └── python.exe
```

The bridge supports either the flat or nested MCP server layout. **Do not rename `maitri_mcp_server.py`, `maitri_mcp_bridge.py`, or the configured Vosk folder without also updating the paths in the code.**

Virtual environments are machine-specific and should generally not be committed to GitHub. Create a fresh `.venv` on the target computer instead.

---

## 7. Install everything from a clean Windows computer

These steps assume you have copied or cloned the complete Maitri project folder.

### Step 1 — Install Python 3.14

1. Open https://www.python.org/downloads/windows/.
2. Download the 64-bit Windows installer for Python 3.14.
3. Run the installer.
4. Enable the option to install the Python launcher if offered.
5. Finish installation.
6. Open **Command Prompt** and verify:

```bat
py -0p
py -3.14 --version
```

The second command should print a Python 3.14 version. If it says that the requested version cannot be found, install Python 3.14 before continuing.

> This project has previously been run with multiple Python versions installed. Always use the same interpreter for installing a package and running the code that imports it. `pip install` with one Python version does not install that package into every other Python version.

### Step 2 — Install Ollama

1. Download Ollama from https://ollama.com/download/windows.
2. Install it.
3. Start Ollama. It may run in the system tray.
4. Open Command Prompt and download the model:

```bat
ollama pull qwen2.5:7b
```

5. Confirm the model is available:

```bat
ollama list
```

6. Test a local response:

```bat
ollama run qwen2.5:7b
```

Type a short question. Exit the interactive session with `/bye` when finished.

If Ollama is not reachable, start Ollama and verify that its local API is responding:

```bat
curl http://127.0.0.1:11434/api/tags
```

The command should return JSON containing the installed model list. Do not continue until the model is downloaded and Ollama responds.

### Step 3 — Install the main Python packages

Open Command Prompt and move into the Maitri project folder. Example:

```bat
cd /d "%USERPROFILE%\Downloads\Maitri"
```

Use the actual location of your folder if it is different. Then run:

```bat
py -3.14 -m pip install --upgrade pip
py -3.14 -m pip install sounddevice numpy vosk pyttsx3 pywin32
```

Check that the modules can be imported:

```bat
py -3.14 -c "import sounddevice, numpy, vosk, pyttsx3; print('Audio and speech packages OK')"
```

If this command fails, read the full error. It usually means a package did not install into Python 3.14, or a dependency could not be installed.

### Step 4 — Install the English Vosk model

1. Open https://alphacephei.com/vosk/models.
2. Download **`vosk-model-small-en-us-0.15`**.
3. Extract the ZIP file.
4. Put the extracted model folder beside `app.py`.

The final path must look like:

```text
Maitri\vosk-model-small-en-us-0.15\
```

Do not leave it as a nested path such as:

```text
Maitri\vosk-model-small-en-us-0.15\vosk-model-small-en-us-0.15\
```

The app checks for the model directory directly beside `app.py`.

### Step 5 — Create the MCP virtual environment

The app expects the MCP server to have a virtual environment containing the MCP SDK. If the MCP server is beside `app.py`, run these commands from the project folder:

```bat
py -3.14 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install "mcp>=1.9,<2.0"
.venv\Scripts\python.exe -c "from mcp.server.fastmcp import FastMCP; print('MCP SDK OK')"
```

If the server is in `Maitri_MCP_Starter`, use that folder instead:

```bat
cd Maitri_MCP_Starter
py -3.14 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install "mcp>=1.9,<2.0"
.venv\Scripts\python.exe -c "from mcp.server.fastmcp import FastMCP; print('MCP SDK OK')"
cd ..
```

Use only the version of the server file included with the app build. Do not accidentally pair an old starter server with a different server file that exposes different tool names.

### Step 6 — Install the Hindi Pocket TTS dependencies

1. Confirm that `indus-pocket-tts` is present beside `app.py`.
2. Confirm that `indus-pocket-tts\speak.py` exists.
3. Follow the dependency installation instructions bundled with that exact TTS folder, if provided.
4. Ensure the TTS script can be launched by Python 3.14.

The known smoke test for the installed project version is:

```bat
py -3.14 indus-pocket-tts\speak.py "नमस्ते! मैं मैत्री हूँ। आप कैसे हैं?" hindi_test.wav --int8
```

If successful, the script should create `hindi_test.wav`. Play the WAV file to verify that audio was generated. Delete the test file when done.

If the script reports missing modules or model files, install the dependencies specified by that TTS package and verify that its required assets are present. Do not guess at package names based on unrelated TTS projects; model packages have a talent for being almost, but not quite, interchangeable.

### Step 7 — Confirm the key files exist

From the project folder:

```bat
dir app.py
dir maitri_mcp_bridge.py
dir maitri_mcp_server.py
dir vosk-model-small-en-us-0.15
dir indus-pocket-tts\speak.py
```

If the MCP server is in the nested folder, check `Maitri_MCP_Starter\maitri_mcp_server.py` and its `.venv\Scripts\python.exe` instead.

---

## 8. Start Maitri

### Option A — Run directly

Open Command Prompt in the project folder and run:

```bat
py -3.14 app.py
```

Keep Ollama running. The Maitri desktop window should appear.

### Option B — Use the Windows launcher

If the project includes `START_MAITRI_FIXED.bat`, double-click it. That launcher is intended to install/check the core audio dependencies and start `app.py` with Python 3.14.

If the launcher is not included in your repository, use Option A or create a launcher appropriate for your folder. Do not download an unrelated BAT file and assume its paths match your installation.

### What the status label means

- **Local AI connected:** Ollama responds and the configured model is installed.
- **Model not found:** Ollama responds, but `qwen2.5:7b` was not found under the expected model name.
- **Ollama not reachable:** Ollama is not running, its API is unavailable, or a local connection failed.
- **Listening… / Listening for 6 seconds…:** Maitri is recording audio.
- **Maitri is thinking…:** A chat or tool request is being processed.
- **MCP tool completed:** A tool call returned a result.
- **Connection error:** Read the message in the chat and the terminal for details.

---

## 9. Use the desktop interface

### Send a typed message

1. Click the message input field at the bottom.
2. Type a question or request.
3. Press **Enter** or click **Send**.
4. Wait for the response.

Examples:

- `Explain photosynthesis in simple words.`
- `Help me plan a revision session.`
- `नमस्ते मैत्री, तुम कैसी हो?`
- `Explain this in Hinglish.`

Maitri sends ordinary conversation to the local Qwen model. Model output may still be incorrect, incomplete, or out of date.

### Toggle speech

Use the **Speak replies** checkbox to enable or disable spoken responses. This affects speech output, not microphone recording or speech recognition.

### Keep conversations in context

Messages are kept in the app's in-memory conversation list while the process is running. This allows later messages to refer to earlier messages during that session. The current code does not provide a dedicated conversation-history browser or a persistent chat archive.

---

## 10. Use voice input and spoken replies

### Microphone input

1. Connect a microphone and allow Windows to use it.
2. Open Maitri.
3. Click **Speak (6 sec)**.
4. Speak clearly during the recording window.
5. Wait for Vosk to transcribe the recording.
6. Read the displayed `I heard: ...` transcript.
7. Maitri submits the recognized text as a normal message.

The current UI records a fixed six-second clip. It does not continuously listen for a wake word, and it does not provide always-on background listening.

### English speech output

For non-Devanagari responses, the app uses `pyttsx3` with Windows SAPI5. It attempts to select a voice that appears to be female or whose name matches a small list of common Windows voices, then sets the speaking rate and volume.

The available voice depends on the Windows installation. If a suitable voice is not installed, Windows may use its default voice.

### Hindi speech output

If the response contains Devanagari characters, the app calls:

```bat
py -3.14 indus-pocket-tts\speak.py "<response text>" "<temporary wav file>" --int8
```

It then plays the generated WAV using Windows audio playback and attempts to remove the temporary file. This requires the local Hindi TTS script, its model/dependencies, and Python 3.14 to work correctly.

### Language and recognition limits

- The configured Vosk microphone model is English. It is not the Hindi Vosk model.
- The language model can generate Hindi or Hinglish text, but this does not mean the microphone recognizer can reliably transcribe spoken Hindi.
- Hindi voice output and Hindi voice input are separate systems.
- Numbers, IDs, punctuation, names, and noisy speech may be recognized incorrectly. Verify the transcript before relying on a command.
- The speech output decision checks for Devanagari characters. Romanized Hinglish without Devanagari will follow the English Windows TTS path.

---

## 11. Use the MCP tools

Maitri exposes four local MCP tools. The local model may route a natural-language request to a tool when it identifies a clear action. Exact supported phrases are not the only way to invoke a tool, but natural-language routing can make mistakes.

### Tool 1 — `get_current_time`

**Purpose:** Return the computer's current local date, time, and timezone.

Try:

- `What time is it right now?`
- `Could you tell me the current time?`
- `Date and time`
- `Abhi time kya hai?`

The result comes from the computer's local clock. Check Windows date, time, and timezone settings if the result is wrong.

### Tool 2 — `add_study_task`

**Purpose:** Save a study task with an optional due-time note.

Try:

- `Add a task to revise maths tomorrow.`
- `Please add a task to finish chapter 4.`
- `Remind me to practise physics tomorrow at 6 PM.`

The intent router extracts a task title and may store the time phrase as a note. Check the returned task ID and title.

**This is task tracking, not an alarm.** The words `tomorrow` or `at 6 PM` are stored as text; the current tool does not parse them into a timestamp, start a scheduler, or notify you later.

### Tool 3 — `list_study_tasks`

**Purpose:** Show saved tasks.

Try:

- `What study tasks are still open?`
- `Show my study tasks.`
- `List my tasks.`
- `List all tasks, including completed ones.`

Open tasks are listed by default. Requests mentioning completed tasks or all tasks can ask the router to include completed entries. If the output seems incomplete, ask explicitly to include completed tasks.

### Tool 4 — `complete_study_task`

**Purpose:** Mark a task complete using its numeric ID.

1. List tasks.
2. Find the numeric ID, such as `#2`.
3. Say or type `Mark task 2 as complete.` or `Complete task 2.`
4. Check the response to ensure the correct task was marked.

The task ID is the number, not the task title. The tool reports if the ID does not exist or is already complete. Avoid relying on voice transcription for IDs without checking what Maitri heard.

### How task data is stored

Tasks are saved in:

```text
%USERPROFILE%\.maitri\study_tasks.json
```

This expands to a `.maitri` directory inside your Windows user profile. The file is created when a task operation needs it. It is a normal JSON file, so it can be backed up or inspected with a text editor. Close Maitri before manually editing the file, and preserve valid JSON syntax.

### What the MCP integration does not do

- It does not expose arbitrary shell commands as tools.
- It does not give Maitri unrestricted control of Windows.
- It does not call a cloud MCP service in the described build.
- It does not automatically schedule tasks.
- It does not automatically sync task data to another computer.

---

## 12. Task storage, privacy, and backups

### Where data lives

- Task records: `%USERPROFILE%\.maitri\study_tasks.json`
- Chat history: in memory while the app is running; no persistent chat archive is implemented by this build.
- Vosk, Ollama, and TTS models: stored in their installation/model folders.

### Back up study tasks

1. Close Maitri.
2. Press `Win + R`.
3. Enter `%USERPROFILE%\.maitri` and press Enter.
4. Copy `study_tasks.json` to a safe backup location.

To restore, close Maitri and copy the backup file back into that folder. Keep a separate copy before changing the server or task format.

### Privacy characteristics

Normal chat inference is sent to the Ollama API on the same machine using a loopback address. Speech recognition uses the local Vosk model. The Hindi TTS workflow is intended to use local assets. These characteristics support offline use after installation, but you should verify the exact dependencies and configuration in any redistributed build.

No application can promise that a computer is completely private in every circumstance. Operating-system services, network configuration, other installed software, crash logs, or changes made by a future version can affect data handling. This manual does not claim that all network traffic from Windows or every dependency is blocked.

---

## 13. Configuration reference

The current app defines these settings near the top of `app.py`:

| Setting | Current value | Meaning |
|---|---|---|
| `OLLAMA_URL` | `http://127.0.0.1:11434/api/chat` | Local Ollama chat endpoint |
| `MODEL` | `qwen2.5:7b` | Required Ollama model name |
| `VOSK_MODEL_PATH` | `vosk-model-small-en-us-0.15` beside `app.py` | English speech-recognition model folder |
| MCP server path | Flat folder or `Maitri_MCP_Starter` subfolder | Where the MCP server file is found |
| MCP Python path | `.venv\Scripts\python.exe` beside the MCP server | Python interpreter used to launch the MCP bridge/server |
| Hindi TTS script | `indus-pocket-tts\speak.py` | Local Hindi speech-generation script |
| Hindi TTS interpreter | `py -3.14` | Python version used to launch Hindi TTS |
| Recording duration | 6 seconds | Fixed microphone recording length |
| Window title | `Maitri` | Desktop window title |

If you edit any of these values, test the affected feature afterwards. Avoid changing multiple paths and dependencies at once; otherwise troubleshooting becomes an archaeological expedition.

---

## 14. Troubleshooting

### A. `py -3.14` is not recognized or Python 3.14 cannot be found

Run:

```bat
py -0p
```

Install Python 3.14 64-bit and confirm that it appears in the list. If the Python launcher is missing, reinstall Python with the launcher option or use the full path to the correct interpreter. Do not substitute a different version without retesting the TTS path and dependencies.

### B. `ModuleNotFoundError: No module named 'sounddevice'`

Install into the exact interpreter used to launch Maitri:

```bat
py -3.14 -m pip install sounddevice
py -3.14 -c "import sounddevice; print('sounddevice OK')"
```

Repeat the same pattern for other missing packages. A package installed into Python 3.15, for example, is not automatically available in Python 3.14.

### C. Ollama is not reachable

1. Start Ollama.
2. Run `ollama list`.
3. Confirm `qwen2.5:7b` is present.
4. Test `curl http://127.0.0.1:11434/api/tags`.
5. If the model is missing, run `ollama pull qwen2.5:7b`.
6. Restart Maitri.

### D. `Model not found`

The app checks for the configured model name. Run:

```bat
ollama list
```

If you downloaded a different tag, either pull the expected tag or update `MODEL` in `app.py` to the installed tag and test it.

### E. Microphone button reports a Vosk model missing

Ensure this exact directory is next to `app.py`:

```text
vosk-model-small-en-us-0.15
```

Extract the downloaded archive rather than pointing the app at the ZIP. Check that the folder contains the Vosk model files and is not accidentally nested one directory deeper.

### F. Microphone records but transcription is empty or wrong

- Check the Windows microphone input device and privacy permissions.
- Speak close to the microphone in a quiet room.
- Avoid covering the microphone.
- Remember that this build uses an English Vosk model.
- Check the displayed transcript before allowing a tool action.
- Try another microphone if the recorded signal is too quiet.

### G. English speech output fails

Install the relevant packages into Python 3.14:

```bat
py -3.14 -m pip install pyttsx3 pywin32
py -3.14 -c "import pyttsx3; print('pyttsx3 OK')"
```

Confirm that Windows has an available SAPI5 voice and that audio output is not muted. Launch the app from Command Prompt to inspect any printed error. If `pythoncom` is missing, install `pywin32` in the same environment.

### H. Hindi speech output fails

Check the following:

1. `indus-pocket-tts\speak.py` exists.
2. Python 3.14 is installed and callable with `py -3.14`.
3. The TTS package dependencies and model assets are installed.
4. The standalone Hindi TTS smoke test in Section 7 succeeds.
5. The output folder is writable and Windows can play WAV audio.

The application displays a speech error in the status label and prints details to the terminal when possible. Fix the standalone TTS test first, then test the app.

### I. MCP tools fail or report that the server is missing

Check that all three files are in the supported places:

- `app.py`
- `maitri_mcp_bridge.py`
- `maitri_mcp_server.py`

Then confirm the MCP virtual environment is beside the server and includes the SDK:

```bat
.venv\Scripts\python.exe -c "from mcp.server.fastmcp import FastMCP; print('MCP SDK OK')"
```

If using a nested server folder, run that command from the nested folder. Verify that the bridge and server are from compatible project versions.

### J. MCP SDK installation fails

Activate the correct virtual environment or call its Python directly. Recommended command:

```bat
.venv\Scripts\python.exe -m pip install "mcp>=1.9,<2.0"
```

If you are using a nested layout, adjust the path accordingly. Read the entire pip error; network, certificate, proxy, Python-version, and package-resolution failures need different fixes.

### K. Natural-language commands go to chat instead of a tool

The intent router is probabilistic and can fail to identify an action. Try a clear request such as:

- `What time is it right now?`
- `Add a task to revise maths tomorrow.`
- `What study tasks are still open?`
- `Mark task 2 as complete.`

Check the response and task list. The phrase fallback covers only a subset of possible wording. Do not assume every synonym will be recognized.

### L. A task does not create a reminder

That is expected in the documented build. A due phrase is stored as a note, and no scheduler is implemented. Do not use the task list as a safety-critical alarm or deadline notification system.

### M. Maitri opens and closes immediately

Start it from Command Prompt so the error stays visible:

```bat
cd /d "C:\path\to\Maitri"
py -3.14 app.py
```

Replace the example path with the real project path. Copy the complete traceback before changing files.

### N. The app works on one computer but not another

Check the Python version, installed packages, Ollama model, Vosk model directory, Hindi TTS assets, MCP virtual environment, and relative folder layout. A virtual environment copied from another computer may contain invalid paths; recreate it on the new computer.

---

## 15. Testing checklist

Run this checklist after a clean install or code change.

### Installation and local AI

- [ ] `py -3.14 --version` reports Python 3.14.
- [ ] `ollama list` shows `qwen2.5:7b`.
- [ ] `curl http://127.0.0.1:11434/api/tags` returns model JSON.
- [ ] Maitri opens and reports the local AI connection.

### Text chat

- [ ] Send an ordinary question and receive a reply.
- [ ] Send a follow-up that refers to the prior message.
- [ ] Confirm that ordinary conversation does not trigger a task tool unnecessarily.

### Voice

- [ ] Click **Speak (6 sec)** and speak English.
- [ ] Confirm the transcript appears in the input flow.
- [ ] Confirm Maitri replies.
- [ ] Confirm English speech output works.
- [ ] Confirm a Devanagari Hindi reply uses the Hindi TTS path.
- [ ] Toggle **Speak replies** off and verify replies are no longer spoken.

### MCP tools

- [ ] Ask for the current time.
- [ ] Add a study task and record its task ID.
- [ ] List open tasks.
- [ ] List completed tasks as well.
- [ ] Complete an existing task by ID.
- [ ] Confirm the task remains saved after closing and reopening Maitri.
- [ ] Try a voice request for the current time and verify the tool result is spoken when speech is enabled.

### Negative checks

- [ ] Stop Ollama and verify the app reports a useful connection error.
- [ ] Temporarily test the missing-model path only if safe to do so, then restore the model directory.
- [ ] Test a nonexistent task ID and confirm no unrelated task is changed.
- [ ] Verify that a due phrase is treated as a note, not an actual scheduled notification.

---

## 16. Security and limitations

- The MCP server offers a narrow set of tools; it should remain limited to the actions the app actually needs.
- The natural-language router uses a strict allowlist. Preserve that restriction when adding tools.
- Do not add arbitrary shell execution, unrestricted filesystem access, or unrestricted browser control without a careful threat model and explicit permission checks.
- The app accepts model output as conversational text. A local model can still produce incorrect claims or misinterpret instructions.
- Voice transcription errors can cause the wrong request to be sent. Confirm important actions and IDs.
- Protect `%USERPROFILE%\.maitri\study_tasks.json` if task titles contain private information.
- Keep dependencies updated and pin tested versions in a real release. This manual's MCP SDK range reflects the working setup described here, not a guarantee that every future version will behave identically.
- Do not commit virtual environments, secrets, private user data, or large model files to a public repository unless you have a deliberate reason and permission to distribute them.
- Review the licenses and redistribution terms for the language model, Vosk model, Pocket TTS code/assets, and every dependency before publishing or redistributing them.

---

## 17. Project structure and responsibilities

| File or folder | Responsibility |
|---|---|
| `app.py` | Tkinter desktop UI, chat history for the active session, Ollama calls, microphone recording/transcription, speech output, and MCP intent routing |
| `maitri_mcp_bridge.py` | Starts the MCP client session, connects over stdio, invokes a named tool, and returns text |
| `maitri_mcp_server.py` | Defines the four MCP tools and reads/writes the task JSON file |
| `.venv/` | Isolated Python environment for the MCP SDK and bridge/server process |
| `vosk-model-small-en-us-0.15/` | Offline English speech-recognition model |
| `indus-pocket-tts/` | Hindi speech-generation script and its dependencies/assets |
| `START_MAITRI_FIXED.bat` | Optional convenience launcher for the tested Windows/Python setup |
| `%USERPROFILE%\.maitri\study_tasks.json` | Persistent study task records |

### Task record fields

The current server saves records with fields similar to:

- `id`: numeric task identifier.
- `title`: task description.
- `due`: optional plain-text due note.
- `completed`: whether the task is marked complete.
- `created_at`: local timezone-aware timestamp in ISO format.
- `completed_at`: timestamp added when a task is completed.

The exact fields in an existing file may vary if it was created by a different version. Back it up before changing the server's data format.

---

## 18. Reproducibility checklist for maintainers

Before publishing a release or handing the project to another developer:

1. Include the current `app.py`, `maitri_mcp_bridge.py`, `maitri_mcp_server.py`, and this README.
2. Include a `requirements.txt` for the main app's Python dependencies and separate documented setup for the MCP virtual environment.
3. Document the exact Python version used for each component.
4. Document the Ollama model tag and the steps to download it.
5. Provide the exact Vosk model name and official download link.
6. Include the Hindi TTS source, required assets, dependency instructions, and licensing information, or clearly state how to obtain them.
7. Verify the folder layout and all paths on a clean Windows account.
8. Run the full testing checklist above.
9. Confirm the project runs after reboot and with the network disconnected after installation, if offline operation is a project claim.
10. State known limitations plainly, especially that task due notes do not create scheduled reminders.
11. Review all third-party model and dependency licenses before public distribution.
12. If the hackathon has a required SDK, API, protocol version, or transport, verify those requirements independently. This build's MCP bridge uses **stdio transport**; do not describe it as an HTTP-hosted MCP server.

---

## Quick-start summary

After completing the full installation once:

1. Start Ollama.
2. Confirm `qwen2.5:7b` is installed.
3. Open Command Prompt in the Maitri folder.
4. Run:

```bat
py -3.14 app.py
```

5. Type a question, or click **Speak (6 sec)** to use the microphone.
6. Leave **Speak replies** enabled if you want spoken responses.
7. Try `What time is it right now?`, `Add a task to revise maths tomorrow.`, and `What study tasks are still open?`.
8. Remember: study tasks persist locally, but due notes are not scheduled reminders.

**Maitri is intended to keep its AI chat and core speech workflow local once installed. Its exact offline behaviour depends on the assets, dependencies, and configuration shipped with the version you run.**
