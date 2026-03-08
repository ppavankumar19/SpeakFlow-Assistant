# AI Voice Chat

An interactive AI chat application powered by **Ollama** (local LLM) with full **voice input and output** support.
When you speak via the mic, the AI replies with **voice only** — no text shown.
When you type, you get a normal text chat experience.

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
├── .env                   # Local secrets/config (not committed)
├── start.sh               # One-command startup script
└── README.md
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

Create your local env file:

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

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Check Ollama and Sarvam.ai status |
| `GET` | `/api/models` | List installed Ollama models |
| `POST` | `/api/chat` | Streaming chat (SSE) |
| `POST` | `/api/stt` | Speech-to-text via Sarvam.ai |
| `POST` | `/api/tts` | Text-to-speech via Sarvam.ai |

---

## Voice Providers

| Provider | STT | TTS | Requires Key |
|---|---|---|---|
| **Browser (built-in)** | Web Speech API | SpeechSynthesis API | No |
| **Sarvam.ai** | `saarika:v2.5` model | `bulbul:v2` model (`anushka` voice) | Yes |

Switch providers from the **Voice Settings** panel in the sidebar.

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
