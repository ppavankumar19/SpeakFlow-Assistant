#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_DIR="$PROJECT_DIR/.venv"

echo "========================================"
echo "   AI Voice Chat - Startup"
echo "========================================"

# 0. Ensure .env exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
  if [ -f "$PROJECT_DIR/.env.example" ]; then
    echo "[INFO] .env not found. Creating from .env.example..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
  else
    echo "[WARN] .env not found. Create one with OLLAMA_BASE_URL, OLLAMA_MODEL, and SARVAM_API_KEY."
  fi
fi

# 1. Check Ollama
if ! command -v ollama &>/dev/null; then
  echo "[WARN] Ollama not found. Install from https://ollama.com"
  echo "       Then run: ollama pull llama3.2"
else
  echo "[OK] Ollama found"
  # Pull model if not present
  if ! ollama list | grep -q "llama3.2"; then
    echo "[INFO] Pulling llama3.2 (first time, ~2GB)..."
    ollama pull llama3.2
  fi
fi

# 2. Create virtualenv if needed
if [ ! -d "$VENV_DIR" ]; then
  echo "[INFO] Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# 3. Install dependencies
echo "[INFO] Installing Python dependencies..."
"$VENV_DIR/bin/pip" install -q -r "$BACKEND_DIR/requirements.txt"

# 4. Check .env
if [ -f "$PROJECT_DIR/.env" ] && \
   (grep -q "PASTE_YOUR_KEY_HERE" "$PROJECT_DIR/.env" || ! grep -Eq '^SARVAM_API_KEY=.+$' "$PROJECT_DIR/.env"); then
  echo ""
  echo "[WARN] Sarvam.ai API key not set!"
  echo "       Edit .env and replace PASTE_YOUR_KEY_HERE with your key."
  echo "       Voice features will use browser fallback until then."
  echo ""
fi

# 5. Start backend
echo "[INFO] Starting server at http://localhost:8000 ..."
echo ""
cd "$BACKEND_DIR"
"$VENV_DIR/bin/uvicorn" main:app --host 0.0.0.0 --port 8000 --reload
