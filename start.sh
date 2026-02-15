#!/bin/sh
# Single script: deps -> Ollama load/run -> server -> frontend opens in browser.
# Run: ./start.sh
# Requires: Ollama (https://ollama.com), Python

set -e
cd "$(dirname "$0")"

# ---- 1. Install dependencies ----
echo "[1/4] Checking dependencies..."
if [ -d venv ]; then
  . venv/bin/activate
else
  python3 -m venv venv && . venv/bin/activate
  pip install -r requirements.txt -q
fi
echo "      Dependencies OK."

# ---- 2. Ollama: load and run ----
echo "[2/4] Checking Ollama..."
if ! curl -s -f "http://localhost:11434/api/tags" >/dev/null 2>&1; then
  if command -v ollama >/dev/null 2>&1; then
    echo "      Starting Ollama in background..."
    ollama serve &
    sleep 5
    echo "      Ollama is up."
  else
    echo "      Ollama not found. Install from https://ollama.com and re-run ./start.sh"
    echo "      Starting app anyway."
  fi
else
  echo "      Ollama is already running."
fi

# ---- 3. Pull model from web (ollama pull phi3:mini - small, fast) ----
if curl -s -f "http://localhost:11434/api/tags" >/dev/null 2>&1; then
  echo "[3/4] Pulling model phi3:mini from web (small, fast download)..."
  if command -v ollama >/dev/null 2>&1; then
    ollama pull phi3:mini
    echo "      Model phi3:mini OK."
  else
    python3 scripts/ensure_model.py || true
    echo "      Model OK (or skipped)."
  fi
else
  echo "[3/4] Skipping model (Ollama not running). Run ./start.sh after installing Ollama."
fi

# ---- 4. Start server and open frontend in browser ----
echo "[4/4] Starting server and opening frontend..."
echo "      Server: http://localhost:8000 (browser will open automatically)"
exec python3 run.py
