# amazon-dev-hackthon

## Prerequisites

- Python 3.11 or newer
- [Ollama](https://ollama.com/download)
- The Qwen model used by this project

## Setup

1. Install and start Ollama.
2. Download the required model:

   ```bash
   ollama pull qwen3.8:27b
   ```

3. Clone this repository:

   ```bash
   git clone YOUR_GITHUB_REPOSITORY_URL
   cd YOUR_PROJECT_FOLDER
   ```

4. Create a virtual environment and install dependencies:

   ```bash
   py -m venv .venv
   .venv\Scripts\activate
   py -m pip install -r requirements.txt
   ```

5. Copy `.env.example` to `.env` and configure:

   ```env
   OLLAMA_BASE_URL=http://127.0.0.1:11434
   OLLAMA_MODEL=qwen3.8:27b
   ```

6. Start the application using the command
   documented by this project.
