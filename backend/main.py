import os
import json
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

http_client: httpx.AsyncClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=120.0)
    yield
    await http_client.aclose()

app = FastAPI(title="Ollama Voice Chat", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")
SARVAM_API_KEY  = os.getenv("SARVAM_API_KEY", "")
SARVAM_BASE_URL = "https://api.sarvam.ai"


# ─── Models ──────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    model: str = ""
    history: list[ChatMessage] = []

class TTSRequest(BaseModel):
    text: str
    language: str = "en-IN"
    speaker: str = "anushka"


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    ollama_ok = False
    try:
        r = await http_client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
        ollama_ok = r.status_code == 200
    except Exception:
        pass

    return {
        "ollama": "connected" if ollama_ok else "disconnected",
        "sarvam": "configured" if SARVAM_API_KEY else "not configured",
        "default_model": OLLAMA_MODEL,
    }


# ─── Models list ─────────────────────────────────────────────────────────────

@app.get("/api/models")
async def get_models():
    try:
        r = await http_client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10.0)
        if r.status_code == 200:
            data = r.json()
            names = [m["name"] for m in data.get("models", [])]
            return {"models": names, "default": OLLAMA_MODEL}
    except Exception:
        pass
    return {"models": [OLLAMA_MODEL], "default": OLLAMA_MODEL}


# ─── Chat (streaming) ─────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if len(request.message) > 8000:
        raise HTTPException(status_code=400, detail="Message too long (max 8000 characters)")
    model = request.model or OLLAMA_MODEL
    messages = [{"role": m.role, "content": m.content} for m in request.history]
    messages.append({"role": "user", "content": request.message})

    async def generate():
        try:
            async with http_client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/chat",
                json={"model": model, "messages": messages, "stream": True},
                timeout=120.0,
            ) as resp:
                if resp.status_code != 200:
                    yield f"data: {json.dumps({'error': f'Ollama returned {resp.status_code}'})}\n\n"
                    return
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield f"data: {json.dumps({'content': content})}\n\n"
                        if data.get("done"):
                            yield f"data: {json.dumps({'done': True})}\n\n"
                    except json.JSONDecodeError:
                        pass
        except httpx.ConnectError:
            yield f"data: {json.dumps({'error': 'Cannot reach Ollama. Is it running? (ollama serve)'})}\n\n"
        except (httpx.RemoteProtocolError, httpx.ReadError):
            pass  # client disconnected mid-stream
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ─── Speech-to-Text (Sarvam) ─────────────────────────────────────────────────

@app.post("/api/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    if not SARVAM_API_KEY:
        raise HTTPException(status_code=400, detail="SARVAM_API_KEY not set in .env")

    audio_bytes = await audio.read()
    try:
        resp = await http_client.post(
            f"{SARVAM_BASE_URL}/speech-to-text",
            headers={"api-subscription-key": SARVAM_API_KEY},
            files={"file": (audio.filename or "audio.wav", audio_bytes, audio.content_type or "audio/wav")},
            data={"language_code": "en-IN", "model": "saarika:v2.5"},
            timeout=30.0,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Sarvam STT: {resp.text}")
        return resp.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Text-to-Speech (Sarvam) ─────────────────────────────────────────────────

@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    if not SARVAM_API_KEY:
        raise HTTPException(status_code=400, detail="SARVAM_API_KEY not set in .env")

    # Sarvam TTS has a ~500 char limit per input chunk
    text = request.text[:500]

    try:
        resp = await http_client.post(
            f"{SARVAM_BASE_URL}/text-to-speech",
            headers={
                "api-subscription-key": SARVAM_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "inputs": [text],
                "target_language_code": request.language,
                "speaker": request.speaker,
                "pitch": 0,
                "pace": 1.0,
                "loudness": 1.5,
                "speech_sample_rate": 22050,
                "enable_preprocessing": True,
                "model": "bulbul:v2",
            },
            timeout=30.0,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Sarvam TTS: {resp.text}")
        data = resp.json()
        audios = data.get("audios", [])
        return {"audio": audios[0] if audios else None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Serve frontend ───────────────────────────────────────────────────────────

app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), '..', 'frontend'), html=True), name="frontend")
