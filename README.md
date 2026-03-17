# AI Voice Chat

An interactive AI chat application powered by **Ollama** (local LLM) with full **voice input and output** support.
When you speak via the mic, the AI replies with **voice only** — no text shown.
When you type, you get a normal streaming text chat experience.

---

## Features

| Feature | Description |
|---|---|
| **Voice-only responses** | Speak via mic → AI replies with voice only, no text bubble shown |
| **Animated AI robot logo** | Custom inline SVG robot logo on welcome screen + watermark behind chat |
| **Streaming text chat** | Real-time token-by-token text responses when typing |
| **Voice waveform card** | Animated waveform card shown during voice response with Replay button |
| **Auto-speak (text mode)** | Optionally auto-speak text chat responses too |
| **Dual STT/TTS providers** | Browser built-in (no key needed) or Sarvam.ai (high quality) |
| **Model selector** | Auto-detects all installed Ollama models |
| **Live status indicators** | Ollama and Sarvam.ai connection status in sidebar |
| **Quick-start chips** | One-click starter prompts on welcome screen |
| **New / Clear chat** | Reset conversation history at any time |
| **Responsive UI** | Works on desktop and mobile |

---

## Project Structure

```
ollama-chat/
├── backend/
│   ├── main.py            # FastAPI server — chat, STT, TTS endpoints
│   └── requirements.txt   # Python dependencies
├── frontend/
│   └── index.html         # Single-file UI (HTML + CSS + JS)
├── .env.example           # Template for environment variables
├── .env                   # Local secrets/config (never commit this)
├── start.sh               # One-command startup script
└── README.md
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (frontend)                        │
│                     frontend/index.html                          │
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────┐   │
│  │  Voice Input │   │  Text Input  │   │  Settings Sidebar  │   │
│  │  (Mic btn)   │   │  (Textarea)  │   │  model / TTS / STT │   │
│  └──────┬───────┘   └──────┬───────┘   └────────────────────┘   │
│         │                  │                                      │
│         └──────────────────▼──────────────────────               │
│                    sendMessage(isVoice)                           │
│                         │                                        │
│              ┌──────────▼──────────┐                             │
│              │   POST /api/chat    │  (SSE streaming)            │
│              │  + history array    │                             │
│              └──────────┬──────────┘                             │
│                         │  stream tokens                         │
│              ┌──────────▼──────────┐                             │
│              │  Text bubble  OR    │                             │
│              │  Voice waveform card│                             │
│              └──────────┬──────────┘                             │
│                         │  if voice / auto-speak                 │
│              ┌──────────▼──────────┐                             │
│              │   POST /api/tts     │  OR  Browser SpeechSynthesis│
│              │   → play audio      │                             │
│              └─────────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
                          │ HTTP / SSE
┌─────────────────────────▼───────────────────────────────────────┐
│                    FastAPI Backend                                │
│                   backend/main.py  :8000                         │
│                                                                  │
│   /api/health  → checks Ollama + Sarvam.ai status               │
│   /api/models  → lists installed Ollama models                  │
│   /api/chat    → proxies to Ollama, converts to SSE stream      │
│   /api/stt     → forwards audio to Sarvam.ai STT               │
│   /api/tts     → forwards text to Sarvam.ai TTS                │
│   /           → serves frontend/index.html (StaticFiles)        │
└──────────┬──────────────────────────┬───────────────────────────┘
           │                          │
           ▼                          ▼
  ┌─────────────────┐       ┌──────────────────────┐
  │  Ollama (local) │       │   Sarvam.ai (cloud)  │
  │ localhost:11434 │       │   api.sarvam.ai       │
  │                 │       │                      │
  │ POST /api/chat  │       │ /speech-to-text      │
  │ GET  /api/tags  │       │ /text-to-speech      │
  └─────────────────┘       └──────────────────────┘
```

---

## How to Run

### Prerequisites

**1. Python 3.10+**
```bash
python3 --version
```

**2. Ollama** — Install from [https://ollama.com](https://ollama.com), then:
```bash
ollama pull llama3.2
ollama serve          # keep this running in a separate terminal
```

**3. Sarvam.ai API Key** *(optional — browser voices work without it)*
Sign up at [https://sarvam.ai](https://sarvam.ai) and get a free key.

---

### Step 1 — Configure `.env`

```bash
cp .env.example .env
```

Open `.env` and set your values:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
SARVAM_API_KEY=your_actual_key_here
```

Leave `SARVAM_API_KEY` blank to use browser built-in voices automatically.
(`start.sh` will also auto-create `.env` from `.env.example` if missing.)

> **Security**: Never commit `.env` to version control — it contains credentials.

---

### Step 2 — Start the app

```bash
cd ~/ollama-chat
chmod +x start.sh
./start.sh
```

The script will:
- Check that Ollama is installed
- Pull `llama3.2` if not already downloaded
- Create a Python virtual environment
- Install all Python dependencies
- Start the server at **http://localhost:8000**

---

### Step 3 — Open in browser

```
http://localhost:8000
```

---

### Manual Start (without start.sh)

```bash
cd ~/ollama-chat/backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Frontend ↔ Backend Data Flows

### 1. Health Check (on page load)

```
Browser                          FastAPI                    Ollama
  │                                 │                          │
  │── GET /api/health ─────────────▶│                          │
  │                                 │── GET /api/tags ────────▶│
  │                                 │◀─ 200 OK ───────────────│
  │◀─ { ollama, sarvam, model } ───│                          │
  │                                 │
  │  Updates status dots in sidebar │
```

Response shape:
```json
{ "ollama": "connected", "sarvam": "configured", "default_model": "llama3.2" }
```

---

### 2. Text Chat (streaming SSE)

```
Browser                          FastAPI                    Ollama
  │                                 │                          │
  │── POST /api/chat ──────────────▶│                          │
  │   { message, model, history }   │── POST /api/chat ───────▶│
  │                                 │   { model, messages,     │
  │                                 │     stream: true }       │
  │                                 │                          │
  │                                 │◀─ JSON stream ──────────│
  │◀─ SSE stream ──────────────────│  (line-by-line)          │
  │  data: {"content": "Hello"}     │                          │
  │  data: {"content": " there"}    │                          │
  │  data: {"done": true}           │                          │
  │                                 │                          │
  │  Appends tokens to bubble       │                          │
```

Request body:
```json
{
  "message": "What is recursion?",
  "model": "llama3.2",
  "history": [
    { "role": "user",      "content": "Hi" },
    { "role": "assistant", "content": "Hello! How can I help?" }
  ]
}
```

SSE event format (each line from server):
```
data: {"content": "Recursion is"}
data: {"content": " a technique"}
data: {"done": true}
```

---

### 3. Voice Input Flow (Sarvam.ai STT)

```
Browser                          FastAPI                 Sarvam.ai
  │                                 │                        │
  │  MediaRecorder captures audio   │                        │
  │  blobToWav() converts to WAV    │                        │
  │── POST /api/stt ───────────────▶│                        │
  │   multipart: audio=recording.wav│── POST /speech-to-text▶│
  │                                 │   api-subscription-key  │
  │                                 │   model: saarika:v2.5   │
  │                                 │◀─ { transcript } ──────│
  │◀─ { transcript: "..." } ───────│                        │
  │                                 │
  │  msgInput.value = transcript    │
  │  sendMessage(true) → /api/chat  │
```

---

### 4. Voice Input Flow (Browser STT)

```
Browser                          FastAPI
  │                                 │
  │  SpeechRecognition API          │
  │  (Web Speech API — no server)   │
  │                                 │
  │  rec.onresult → transcript      │
  │  sendMessage(true) → /api/chat  │── (same as text chat above)
```

---

### 5. Voice Output Flow (Sarvam.ai TTS)

```
Browser                          FastAPI                 Sarvam.ai
  │                                 │                        │
  │── POST /api/tts ───────────────▶│                        │
  │   { text, language, speaker }   │── POST /text-to-speech▶│
  │                                 │   model: bulbul:v2      │
  │                                 │   speaker: anushka      │
  │                                 │◀─ { audios: [base64] } │
  │◀─ { audio: "<base64 wav>" } ───│                        │
  │                                 │
  │  atob() → Uint8Array → Blob     │
  │  URL.createObjectURL → Audio    │
  │  audio.play()                   │
```

---

### 6. Voice Output Flow (Browser TTS)

```
Browser                          FastAPI
  │                                 │
  │  SpeechSynthesisUtterance       │
  │  window.speechSynthesis.speak() │  (no server call)
  │                                 │
  │  Shows TTS status bar           │
  │  Resolves promise on .onend     │
```

---

### Complete Voice Conversation Flow

```
User clicks Speak
      │
      ▼
Browser or Sarvam STT
  (audio → transcript text)
      │
      ▼
sendMessage(isVoice=true)
  POST /api/chat  ──────────────▶  Ollama LLM
      │                           streaming response
      ▼
  voiceOnly=true?
    YES → Show waveform card (no text)
    NO  → Show streaming text bubble
      │
      ▼
speakText(fullResponse)
  Sarvam TTS or Browser TTS
      │
      ▼
Play audio → waveform card shows "done"
  Replay button appears
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Check Ollama and Sarvam.ai status |
| `GET` | `/api/models` | List installed Ollama models |
| `POST` | `/api/chat` | Streaming chat (Server-Sent Events) |
| `POST` | `/api/stt` | Speech-to-text via Sarvam.ai |
| `POST` | `/api/tts` | Text-to-speech via Sarvam.ai |
| `GET` | `/` | Serves `frontend/index.html` |

### POST /api/chat

**Request:**
```json
{
  "message": "Explain machine learning",
  "model": "llama3.2",
  "history": []
}
```

**Response (SSE stream):**
```
Content-Type: text/event-stream

data: {"content": "Machine"}
data: {"content": " learning"}
data: {"content": " is..."}
data: {"done": true}
```

### POST /api/stt

**Request:** `multipart/form-data` with `audio` file (WAV)

**Response:**
```json
{ "transcript": "What is the weather today" }
```

### POST /api/tts

**Request:**
```json
{ "text": "Hello, how can I help?", "language": "en-IN", "speaker": "anushka" }
```

**Response:**
```json
{ "audio": "<base64-encoded WAV>" }
```

---

## Voice Providers

| Provider | STT | TTS | Requires Key |
|---|---|---|---|
| **Browser (built-in)** | Web Speech API | SpeechSynthesis API | No |
| **Sarvam.ai** | `saarika:v2.5` model | `bulbul:v2` model (`anushka` voice) | Yes |

Switch providers from the **Voice Settings** panel in the sidebar.

- Browser providers work offline, no API key needed
- Sarvam.ai provides higher quality, accent-aware Indian English voices
- TTS falls back to Browser automatically if Sarvam.ai fails

---

## Using the App

### Voice Mode (mic button)
1. Click the **Speak** button (or the large mic on the welcome screen)
2. Speak your question clearly
3. Click **Stop Recording**
4. The AI transcribes your speech and replies **via voice only** — a waveform card appears, no text is shown
5. Click **Replay** on the card to hear the response again

### Text Mode (keyboard)
1. Type your message in the text box
2. Press **Enter** to send (Shift+Enter for new line)
3. The AI reply streams as text in the chat
4. Enable **Auto-speak** in the sidebar to also hear text replies

### Sidebar Settings
| Setting | Description |
|---|---|
| **Voice-only responses** | ON = mic input gets voice-only reply; OFF = shows text too |
| **Auto-speak (text mode)** | Speak text replies aloud when typing |
| **TTS Provider** | Browser (free) or Sarvam.ai (high quality) |
| **STT Provider** | Browser (free) or Sarvam.ai (high quality) |

---

## Changing the Ollama Model

Edit `.env`:
```env
OLLAMA_MODEL=mistral
```

Or switch on the fly using the **Model** dropdown in the sidebar.

```bash
ollama list               # see installed models
ollama pull mistral       # download more models
ollama pull gemma2
ollama pull phi3
```

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Enter` | Send message |
| `Shift + Enter` | New line in input |
| Click **Speak** / welcome mic | Start voice recording |
| Click **Stop Recording** | End recording and send |

---

## Troubleshooting

**Ollama shows "disconnected"**
- Ensure Ollama is running: `ollama serve`
- Check it: `curl http://localhost:11434/api/tags`

**Sarvam.ai shows "not configured"**
- Add your key to `.env` and restart the server
- App still works with browser fallback voices

**Microphone not working**
- Allow microphone access when the browser prompts
- Must use `localhost` or HTTPS (browser security requirement)

**Model not responding**
- Ensure the model is downloaded: `ollama pull llama3.2`
- Check Ollama logs in the terminal where `ollama serve` is running

**Voice response not playing**
- Check your system volume and browser audio permissions
- Try switching TTS provider in sidebar (Browser vs Sarvam.ai)

**"No speech detected" after recording**
- Speak closer to the microphone
- Check microphone permissions in browser settings
- Try switching STT provider (Browser vs Sarvam.ai)

---

## Production Notes

- Remove `--reload` from uvicorn in production
- Add workers: `uvicorn main:app --workers 4`
- Restrict CORS origins in `main.py` (`allow_origins=["https://yourdomain.com"]`)
- Use a reverse proxy (nginx) with HTTPS for microphone access from non-localhost
- Ollama runs as a single process — it is a concurrency bottleneck under heavy load
