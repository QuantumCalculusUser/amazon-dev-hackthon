# Maitri Voice + Spoken Replies

This version keeps offline Vosk speech input and adds offline text-to-speech with pyttsx3. It also fixes the visible literal `\n` line-break bug from the earlier version.

## Keep your Vosk model
Put the extracted `vosk-model-small-en-us-0.15` folder beside `app.py`. If it is already in your existing voice-upgrade folder, copy it into this folder too.

## Install dependencies
Open PowerShell in this folder:
```powershell
python -m pip install numpy sounddevice vosk pyttsx3
```

## Run
Make sure Ollama is running and the `qwen2.5:7b` model is available:
```powershell
python app.py
```
The **Speak replies** checkbox enables/disables spoken AI answers. Speech output uses voices installed in Windows; Hindi voice quality depends on whether a Hindi voice is installed. pyttsx3 uses the local Windows speech engine, so it does not require a paid API.
