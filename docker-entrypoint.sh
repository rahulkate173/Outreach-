#!/bin/sh
set -e
echo "Waiting for Ollama..."
python3 -c "
import time, urllib.request
for _ in range(60):
    try:
        urllib.request.urlopen('http://ollama:11434/api/tags', timeout=2)
        break
    except Exception:
        time.sleep(2)
else:
    raise SystemExit('Ollama did not become ready')
"
echo "Ollama is up. Pulling model phi3:mini from web (small, fast)..."
python3 /app/scripts/ensure_model.py
echo "Starting server at http://0.0.0.0:8000"
exec python3 run.py
