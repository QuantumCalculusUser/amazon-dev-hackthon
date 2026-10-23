import threading
import tkinter as tk
from tkinter import ttk, messagebox
import json, urllib.request, urllib.error, os, subprocess, tempfile, re

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen2.5:7b"
VOSK_MODEL_PATH = os.path.join(os.path.dirname(__file__), "vosk-model-small-en-us-0.15")
MCP_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Maitri_MCP_Starter")
MCP_SERVER_PATH = os.path.join(MCP_FOLDER, "maitri_mcp_server.py")
MCP_PYTHON = os.path.join(MCP_FOLDER, ".venv", "Scripts", "python.exe")
MCP_BRIDGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maitri_mcp_bridge.py")
SYSTEM_PROMPT = ("You are Maitri, a helpful desktop assistant. Understand English, Hindi, and Hinglish. "
                "Reply naturally in the language the user uses. Be concise unless asked for detail.")

class MaitriApp:
    def __init__(self, root):
        self.root=root
        root.title("Maitri")
        root.geometry("850x660")
        root.minsize(620,480)
        root.configure(bg="#10151d")
        self.messages=[{"role":"system","content":SYSTEM_PROMPT}]
        self.busy=False
        self.speech_enabled=tk.BooleanVar(value=True)
        style=ttk.Style()
        try: style.theme_use("clam")
        except tk.TclError: pass
        style.configure("TButton",font=("Segoe UI",10),padding=8)
        style.configure("TEntry",font=("Segoe UI",11),padding=8)
        header=tk.Frame(root,bg="#17212e",padx=18,pady=14); header.pack(fill="x")
        tk.Label(header,text="Maitri",font=("Segoe UI",22,"bold"),fg="#f1f5f9",bg="#17212e").pack(side="left")
        tk.Label(header,text="LOCAL AI  •  ENGLISH / हिंदी / HINGLISH",font=("Segoe UI",9),fg="#9fb3c8",bg="#17212e").pack(side="left",padx=16,pady=(8,0))
        self.status=tk.Label(header,text="Checking local AI…",font=("Segoe UI",9),fg="#fbbf24",bg="#17212e"); self.status.pack(side="right",pady=(8,0))
        self.chat=tk.Text(root,wrap="word",state="disabled",font=("Segoe UI",11),bg="#10151d",fg="#e5edf5",insertbackground="white",padx=18,pady=18,relief="flat",spacing1=4,spacing3=10)
        self.chat.pack(fill="both",expand=True,padx=2,pady=2)
        self.chat.tag_configure("you",foreground="#7dd3fc",font=("Segoe UI",10,"bold"))
        self.chat.tag_configure("maitri",foreground="#86efac",font=("Segoe UI",10,"bold"))
        self.chat.tag_configure("body",foreground="#e5edf5")
        bottom=tk.Frame(root,bg="#17212e",padx=12,pady=12); bottom.pack(fill="x")
        self.entry=ttk.Entry(bottom); self.entry.pack(side="left",fill="x",expand=True,padx=(0,8))
        self.entry.bind("<Return>",lambda event:self.send())
        self.mic_btn=ttk.Button(bottom,text="🎙 Speak (6 sec)",command=self.listen); self.mic_btn.pack(side="left",padx=(0,8))
        self.send_btn=ttk.Button(bottom,text="Send",command=self.send); self.send_btn.pack(side="left",padx=(0,8))
        self.speech_check=ttk.Checkbutton(bottom,text="Speak replies",variable=self.speech_enabled); self.speech_check.pack(side="right")
        self.entry.focus_set()
        self.add_line("Maitri","Namaste! I'm Maitri. Type a message or click Speak and talk for up to 6 seconds.")
        threading.Thread(target=self.check_ollama,daemon=True).start()

    def add_line(self,who,text):
        self.chat.configure(state="normal")
        self.chat.insert("end",who+"\n","you" if who=="You" else "maitri")
        self.chat.insert("end",text+"\n\n","body")
        self.chat.configure(state="disabled"); self.chat.see("end")

    def check_ollama(self):
        try:
            with urllib.request.urlopen("http://127.0.0.1:11434/api/tags",timeout=3) as r: data=json.loads(r.read().decode())
            models=[m.get("name","") for m in data.get("models",[])]
            status,color=("Local AI connected","#86efac") if any(m==MODEL or m.startswith(MODEL+":") for m in models) else ("Model not found","#fbbf24")
        except Exception: status,color="Ollama not reachable","#f87171"
        self.root.after(0,lambda:self.status.config(text=status,fg=color))

    def listen(self):
        if self.busy: return
        if not os.path.isdir(VOSK_MODEL_PATH):
            messagebox.showerror("Vosk model not found","Extract vosk-model-small-en-us-0.15 beside app.py. See README.md.")
            return
        self.mic_btn.configure(state="disabled",text="Listening…")
        self.status.config(text="Listening for 6 seconds…",fg="#fbbf24")
        threading.Thread(target=self.record_and_transcribe,daemon=True).start()

    def record_and_transcribe(self):
        try:
            import sounddevice as sd
            from vosk import Model, KaldiRecognizer
            samplerate=16000
            self.root.after(0,lambda:self.add_line("Maitri","Listening now. Speak clearly…"))
            audio=sd.rec(int(6*samplerate),samplerate=samplerate,channels=1,dtype="int16")
            sd.wait()
            recognizer=KaldiRecognizer(Model(VOSK_MODEL_PATH),samplerate)
            recognizer.AcceptWaveform(audio.tobytes())
            result=json.loads(recognizer.FinalResult())
            transcript=result.get("text","").strip()
            if not transcript:
                self.root.after(0,lambda:self.add_line("Maitri","I didn't catch that. Try again and speak closer to the microphone."))
            else:
                self.root.after(0,lambda:self.entry.delete(0,"end"))
                self.root.after(0,lambda:self.entry.insert(0,transcript))
                self.root.after(0,lambda:self.add_line("Maitri","I heard: "+transcript))
                self.root.after(0,self.send)
        except Exception as e:
            msg="Microphone/transcription error: "+str(e)
            self.root.after(0,lambda:messagebox.showerror("Voice input error",msg))
        finally:
            self.root.after(0,lambda:self.mic_btn.configure(state="normal",text="🎙 Speak (6 sec)"))
            self.root.after(0,lambda:self.status.config(text="Local AI connected",fg="#86efac"))

    def speak(self, text):
        """Speak replies using Inaya for Devanagari Hindi and Windows TTS for English."""
        com_initialized = False
        try:
            has_hindi = any("\u0900" <= ch <= "\u097f" for ch in text)
            app_dir = os.path.dirname(os.path.abspath(__file__))
            hindi_script = os.path.join(app_dir, "indus-pocket-tts", "speak.py")

            if has_hindi:
                if not os.path.isfile(hindi_script):
                    raise FileNotFoundError(
                        "Hindi voice script not found: " + hindi_script
                    )
                with tempfile.NamedTemporaryFile(
                    prefix="maitri_hi_", suffix=".wav", delete=False
                ) as tmp:
                    wav_path = tmp.name
                try:
                    result = subprocess.run(
                        ["py", "-3.14", hindi_script, text, wav_path, "--int8"],
                        cwd=app_dir,
                        capture_output=True,
                        text=True,
                        timeout=180,
                    )
                    if result.returncode != 0:
                        details = (result.stderr or result.stdout or "").strip()
                        raise RuntimeError("Hindi TTS failed: " + details)
                    import winsound
                    winsound.PlaySound(wav_path, winsound.SND_FILENAME)
                finally:
                    try:
                        os.remove(wav_path)
                    except OSError:
                        pass
                return

            # pyttsx3/SAPI5 needs COM initialized when called from a background
            # thread. Ollama replies are processed off the Tkinter UI thread.
            try:
                import pythoncom
                pythoncom.CoInitialize()
                com_initialized = True
            except ImportError:
                # Some pyttsx3 installs handle COM setup internally.
                pass

            import pyttsx3
            engine = pyttsx3.init("sapi5")
            try:
                voices = engine.getProperty("voices")
                female_voice = next(
                    (
                        v for v in voices
                        if (getattr(v, "gender", None) or "").lower() == "female"
                        or any(
                            name in (getattr(v, "name", "") or "").lower()
                            for name in ["zira", "hazel", "susan", "heera"]
                        )
                    ),
                    None,
                )
                if female_voice:
                    engine.setProperty("voice", female_voice.id)
                engine.setProperty("rate", 165)
                engine.setProperty("volume", 1.0)
                engine.say(text)
                engine.runAndWait()
            finally:
                engine.stop()
        except Exception as e:
            error_text = "Speech error: " + str(e)
            print(error_text)
            # Surface the error in Maitri instead of silently failing.
            try:
                self.root.after(
                    0,
                    lambda msg=error_text: self.status.config(
                        text=msg[:80], fg="#f87171"
                    ),
                )
            except Exception:
                pass
        finally:
            if com_initialized:
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

    def send(self):
        text=self.entry.get().strip()
        if not text or self.busy: return
        self.entry.delete(0,"end"); self.add_line("You",text)
        self.messages.append({"role":"user","content":text})
        self.busy=True; self.send_btn.configure(state="disabled")
        self.status.config(text="Maitri is thinking…",fg="#fbbf24")
        threading.Thread(target=self.ask_ollama,daemon=True).start()

    def detect_mcp_command(self, text):
        """Map clear, simple user commands to local MCP tools."""
        s = text.strip().lower()

        # Current time/date
        if any(phrase in s for phrase in [
            "what time is it", "current time", "tell me the time",
            "what's the time", "what is the time", "date and time",
            "time kya hai", "kitne baje", "abhi time"
        ]):
            return "get_current_time", {}

        # List tasks
        if any(phrase in s for phrase in [
            "list my tasks", "show my tasks", "show study tasks",
            "list study tasks", "what are my tasks", "my study tasks",
            "mere tasks", "meri tasks", "task dikhao", "tasks dikhao"
        ]):
            include_done = "completed" in s or "all tasks" in s
            return "list_study_tasks", {"include_completed": include_done}

        # Complete task by ID
        match = re.search(r"(?:complete|finish|mark done|done with|complete task)\s*(?:task\s*)?#?\s*(\d+)", s)
        if match:
            return "complete_study_task", {"task_id": int(match.group(1))}

        # Add task. Keep extraction intentionally simple and predictable.
        add_patterns = [
            r"^(?:maitri[, ]+)?(?:add|create|save) (?:a )?(?:study )?task(?: to)?\s+(.+)$",
            r"^(?:maitri[, ]+)?remind me to\s+(.+)$",
            r"^(?:maitri[, ]+)?add task\s*:\s*(.+)$",
            r"^(?:maitri[, ]+)?study task\s*:\s*(.+)$",
        ]
        for pattern in add_patterns:
            match = re.match(pattern, text.strip(), flags=re.IGNORECASE)
            if match:
                detail = match.group(1).strip()
                due = ""
                due_match = re.search(r"\s+(?:at|by|due)\s+(.+)$", detail, flags=re.IGNORECASE)
                if due_match:
                    due = due_match.group(1).strip()
                    detail = detail[:due_match.start()].strip()
                if detail:
                    return "add_study_task", {"title": detail, "due": due}

        return None

    def call_mcp_tool(self, tool_name, arguments):
        """Call the MCP bridge in the isolated MCP virtual environment."""
        if not os.path.isfile(MCP_SERVER_PATH):
            raise FileNotFoundError(
                "MCP server not found. Copy your Maitri_MCP_Starter folder beside app.py."
            )
        if not os.path.isfile(MCP_PYTHON):
            raise FileNotFoundError(
                "MCP virtual environment not found. Expected .venv\\\\Scripts\\\\python.exe "
                "inside the Maitri_MCP_Starter folder."
            )
        if not os.path.isfile(MCP_BRIDGE_PATH):
            raise FileNotFoundError("maitri_mcp_bridge.py must be beside app.py.")
        completed = subprocess.run(
            [MCP_PYTHON, MCP_BRIDGE_PATH, tool_name, json.dumps(arguments, ensure_ascii=False)],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "Unknown MCP error").strip()
            raise RuntimeError(detail)
        return completed.stdout.strip()

    def ask_ollama(self):
        try:
            user_text = self.messages[-1].get("content", "") if self.messages else ""
            tool_request = self.detect_mcp_command(user_text)
            if tool_request:
                tool_name, arguments = tool_request
                answer = self.call_mcp_tool(tool_name, arguments)
                self.messages.append({"role": "assistant", "content": answer})
                self.root.after(0, lambda a=answer: self.add_line("Maitri", a))
                self.root.after(0, lambda: self.status.config(text="MCP tool completed", fg="#86efac"))
                if self.speech_enabled.get():
                    self.speak(answer)
                return

            payload=json.dumps({"model":MODEL,"messages":self.messages,"stream":False}).encode()
            req=urllib.request.Request(OLLAMA_URL,data=payload,headers={"Content-Type":"application/json"},method="POST")
            with urllib.request.urlopen(req,timeout=180) as r: result=json.loads(r.read().decode())
            answer=result.get("message",{}).get("content","").strip() or "(No response returned.)"
            self.messages.append({"role":"assistant","content":answer})
            self.root.after(0,lambda:self.add_line("Maitri",answer))
            self.root.after(0,lambda:self.status.config(text="Local AI connected",fg="#86efac"))
            if self.speech_enabled.get():
                self.speak(answer)
        except Exception as e:
            msg="Couldn't reach Ollama. Make sure it is running. Details: "+str(e)
            self.root.after(0,lambda:self.add_line("Maitri",msg))
            self.root.after(0,lambda:self.status.config(text="Connection error",fg="#f87171"))
        finally:
            self.busy=False
            self.root.after(0,lambda:self.send_btn.configure(state="normal"))
            self.root.after(0,self.entry.focus_set)

if __name__=="__main__":
    root=tk.Tk(); app=MaitriApp(root); root.mainloop()
